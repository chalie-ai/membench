# How We Reduced Our AWS Bill by 67% Without Losing Performance

I remember the exact moment I felt the cold sweat break across my neck. It was a Tuesday morning in October, and I was staring at a CloudWatch dashboard while our CFO, a man who treats every cent like a family heirloom, stood silently behind me. Our monthly AWS bill had just hit $84,000. For a Series B startup with forty engineers and a product that was still finding its footing in the market, that number wasn't just high—it was offensive. It felt like we were paying a "growth tax" that we hadn't actually earned. We weren't serving a billion requests; we were just inefficient.

Managing a cloud budget is a lot like maintaining a garden in a tropical rainforest. If you leave it alone for two weeks, the vines of "temporary" staging environments and oversized RDS instances will literally swallow your entire infrastructure. Most engineers treat the AWS console like a magic vending machine where you put in a credit card and out comes "scalability." But eventually, the bill comes due, and you realize you’ve been buying gold-plated screws for a project that only needed galvanized steel.

Our mission was simple: slash the bill by 50% or more without the site crashing or the developers complaining that their local environments were too slow. We didn't just want to cut costs; we wanted to build a culture of "cost-awareness." Because the moment you stop looking at the bill, the vines grow back. Over the next six months, we managed to drop our monthly spend from $84,000 to roughly $27,700—a 67% reduction—while actually increasing our throughput. Here is exactly how we did it, the mistakes I made along the way, and why your "Auto Scaling Group" is probably lying to you.

## The Great Right-Sizing Massacre

The first thing I realized was that our team suffered from "Instance Anxiety." Every developer wanted the biggest machine possible just in case they hit a spike they didn't know how to debug. We had `m5.4xlarge` instances running APIs that were utilizing 8% of their CPU and 12% of their RAM. We were effectively paying for a fleet of semi-trucks to deliver single envelopes of mail.

We started by implementing a strict right-sizing audit using AWS Compute Optimizer and a third-party tool called Kubecost. I spent two weeks staring at Prometheus metrics, looking for the gap between "Allocated" and "Actual." It turns out that if you tell a developer they have 32GB of RAM, they will use 30GB just because it's there, but if you give them 8GB, they'll optimize their cache and the app will still run perfectly.

We moved our primary API layer from the M-series to the C-series instances, specifically moving to Graviton2 (ARM) processors. This was the single biggest "quick win." Switching to `c6g` instances gave us a better price-performance ratio immediately. The transition wasn't seamless—we had some native binaries that had to be recompiled—but the 20% cost reduction and 15% performance boost were too good to ignore. We stopped guessing and started measuring. If an instance wasn't hitting 40% average CPU utilization over a seven-day window, it got downsized. Period.

## The Reserved Instance Gamble and the Savings Plan Trap

Once we had right-sized the fleet, we had to deal with the "commitment" problem. The mistake most people make is buying Reserved Instances (RIs) based on where they are today, rather than where they will be in a year. I learned this the hard way about three years ago at a previous company where I locked us into a three-year RI contract for a database engine we deprecated six months later. It was a fucking disaster that cost us $40,000 in wasted credits and a very stern conversation with the VP of Engineering.

This time, we avoided the "RI Trap" by using a layered approach. We didn't buy 100% coverage. Instead, we used the "Waterline Strategy." We identified our absolute baseline—the minimum amount of compute we would need even if the world ended—and covered that 40% with a 1-year Compute Savings Plan. This gave us the flexibility to change instance families without losing the discount.

For the more volatile workloads, we looked at the "Marketplace" for RIs. We treated it like a stock market. We waited for the dips and committed to smaller blocks of capacity. The key is to never commit to more than 60% of your peak load. The other 40% should be handled by on-demand or spot instances. If you commit to 100% of your peak, you are paying for idle air during the nighttime troughs. We managed to shave another $12,000 off the monthly bill just by aligning our commitment to our actual baseline.

## Taming the Batch Beast with Spot Instances

Our data processing pipeline was a nightmare. We had a set of heavy batch jobs—essentially "cleaning" our telemetry data—that ran every six hours. We were using on-demand instances for this, which is like paying for a hotel room for a year when you only visit for one weekend a month. 

We migrated these batch jobs to Spot Instances. Now, the traditional fear with Spot is the "interrupt signal"—the moment AWS tells you, "Thanks for playing, we need this server back," and kills your process with a two-minute warning. To solve this, we rebuilt our worker nodes using an "idempotent" architecture. We used a queue-based system where if a worker died, the message simply returned to the queue for another worker to pick up.

We implemented this using a custom Terraform module that managed a mixed instance group. Here is a simplified version of how we configured the capacity rebalance in our ASG:

```hcl
resource "aws_autoscaling_group" "batch_workers" {
  mixed_instances_policy {
    instances_value {
      on_demand_percentage_above_base = 0
      on_demand_base_capacity          = 1
    }
    launch_template {
      launch_template_specification {
        launch_template_id = aws_launch_template.worker_tpl.id
      }
      override {
        instance_type = "c5.xlarge"
      }
      override {
        instance_type = "c5n.xlarge"
      }
    }
  }
}
```

By allowing AWS to pick from a pool of "c5" and "c5n" types, we increased our Spot availability and dropped the cost of our data pipeline by nearly 90%. We went from spending $6,000 a month on batch processing to under $800. The trade-off was a bit more complexity in our error handling, but the ROI was undeniable.

## The Hidden Tax: Data Transfer and NAT Gateways

If you want to find where your money is leaking, look at the "Data Transfer" section of your bill. This is the most insidious part of AWS. We discovered we were spending $4,000 a month on NAT Gateway charges. For those who don't know, a NAT Gateway allows private instances to talk to the internet, but AWS charges you for every gigabyte that passes through it. 

We realized our S3 buckets were in a different region than some of our processing nodes, and we were routing S3 traffic through the NAT Gateway. This is an architectural sin. It's like paying a courier to deliver a letter to your neighbor by driving it to another state and back. 

We fixed this by implementing S3 VPC Endpoints. This allows traffic to stay within the AWS internal network, bypassing the NAT Gateway entirely. The configuration change was trivial, but the impact was immediate. We also stopped using "Public IPs" for our internal service-to-service communication and switched to internal DNS. 

To track this, we started using a tool called Vantage. It gave us a visibility layer that the standard AWS Cost Explorer lacks. We could finally see exactly which microservice was responsible for the data egress. We found one rogue logging agent that was shipping redundant debug logs to an external provider over the internet. Once we killed that process, our egress costs dropped by another $1,200 per month.

## Governance: Stopping the "Cost Creep"

The hardest part of this process wasn't the technical implementation; it was the human element. In a fast-moving startup, "velocity" is the only metric that matters. Engineers will spin up a `p3.16xlarge` instance to train a model for three hours and then forget to turn it off for three months. That is how "Cost Creep" happens.

We implemented a "Cost Governance" framework. First, we mandated that every single AWS resource must have an `Owner` and a `Project` tag. If a resource was found without a tag, a Lambda script (which we nicknamed "The Reaper") would send a Slack notification to the `#eng-alerts` channel. If the resource wasn't tagged within 24 hours, it was automatically stopped. People hated it at first, but it forced everyone to be mindful of what they were deploying.

We also introduced "Cloud Budget Alerts" at the team level. Instead of one giant bill for the company, we split the billing by account. Each team (Platform, Mobile, Backend) had a monthly budget. When they hit 80% of that budget, they got a warning. When they hit 100%, the engineering lead had to justify the overage in the weekly sync. 

This shifted the conversation from "Why is the bill high?" to "Why did the Mobile team's spend spike on Tuesday?" It turned cost optimization into a game of efficiency rather than a corporate mandate. We stopped treating the cloud as an infinite resource and started treating it like a finite budget.

## The Counter-Arguments: Is This Actually Worth It?

Now, I want to address the skeptics. There are two common arguments against this level of aggressive cost optimization. The first is the "Engineer Hour" argument: "The time it takes an engineer to save $2,000 a month is worth more than the $2,000 itself." This is a common trope in Silicon Valley. The logic is that if an engineer makes $150k a year, their time is too valuable to be spent tinkering with NAT Gateways.

This is bullshit. This isn't just about the money; it's about technical discipline. When you optimize for cost, you are almost always optimizing for performance. An application that requires a `m5.4xlarge` to run is usually an application with a memory leak or an inefficient O(n^2) algorithm. By forcing the team to right-size, we actually found three major performance bottlenecks that were slowing down our API response times. The cost optimization was a proxy for a quality audit.

The second argument is that "Spot Instances are too risky for production." To be clear: I agree. You should never run your primary database or your user-facing checkout page on a Spot instance. But the mistake people make is thinking in binaries—either "All On-Demand" or "All Spot." The reality is a spectrum. By using a mixed-instance policy and designing for idempotency, we mitigated the risk. We accepted a 1% chance of a node failure in exchange for a 90% cost reduction on a non-critical background task. That is a trade I will make every single day of the week.

## The Philosophical Shift

If you want to understand the underlying principle of our success, look at the work of Gene Kim in *The Phoenix Project*. He talks about the "Four Ways" of DevOps, and one of the core tenets is the creation of a feedback loop. For months, our feedback loop for cost was "The bill arrives at the end of the month." That is a lagging indicator. By the time you see the bill, the money is already gone.

We moved to a leading indicator system. We integrated cost metrics directly into our Grafana dashboards. Right next to the "Request Latency" and "Error Rate" graphs, we put a "Cost per 1k Requests" graph. This changed the psychology of the team. When a developer pushed a new feature that tripled the memory usage of a pod, they didn't just see a spike in RAM—they saw the cost-per-request climb in real-time.

This approach is similar to the philosophy described in *The Lean Startup* by Eric Ries. We treated our infrastructure as a product. We applied the "Build-Measure-Learn" cycle to our AWS spend. We hypothesized that moving to ARM would save money, we measured the result, and we learned that the performance boost was the real winner.

## Actionable Takeaways for Your Own Bill

If you are staring at a cloud bill that makes you want to quit your job, don't panic. Start with the low-hanging fruit and move toward the structural changes. Here are five specific things you can do this week:

First, audit your "Zombies." Use an open-source tool like `aws-nuke` (carefully!) or a simple script to find unattached EBS volumes and idle Elastic IPs. These are the "ghosts" of deleted instances that continue to haunt your bill.

Second, switch to Graviton (ARM) instances for everything that can support it. The price-performance ratio is simply better. If you are still on x86 for a general-purpose API, you are leaving money on the table.

Third, implement VPC Endpoints for S3 and DynamoDB. Stop paying the NAT Gateway tax. It is a purely administrative cost that provides zero value to your end user.

Fourth, move your non-critical, asynchronous workloads to Spot Instances. Build your applications to be stateless and idempotent. If your app can't survive a server restart, you have a bigger problem than your AWS bill.

Fifth, implement a tagging policy with a "Reaper" mechanism. You cannot manage what you cannot measure. If you don't know who owns a resource, you can't ask them to optimize it.

Reducing our bill by 67% didn't happen overnight, and it didn't happen through a single "magic" setting. It happened because we stopped viewing the cloud as a utility and started viewing it as a resource that requires constant pruning. The garden will always try to overgrow, but as long as you have the tools and the discipline to keep it in check, you can scale your business without scaling your bankruptcy risk.