# Why I Stopped Using Kubernetes for Small Projects

I remember the exact moment my hubris peaked. It was 3:14 AM on a Tuesday in 2019. I was staring at a terminal screen, sweat dripping onto my mechanical keyboard, trying to figure out why a simple health check failure had triggered a cascading restart loop that took down my entire staging environment. I had spent the previous three weeks meticulously crafting a "production-ready" cluster for a project that had exactly twelve active users. Twelve. I wasn't just deploying an app; I was orchestrating a symphony of etcd clusters, ingress controllers, and pods, all for a tool that essentially just moved JSON from a database to a frontend. I felt like a god of infrastructure, until I realized I had spent forty hours configuring the plumbing and zero hours polishing the actual product. I was using a space shuttle to go to the grocery store, and I was the only one paying for the fuel.

For years, I bought into the "Cloud Native" gospel. I read the whitepapers, I followed the CNCF landscape, and I convinced myself that if I didn't have a container orchestrator, I was just writing "legacy code." I viewed the simple VPS—the humble DigitalOcean droplet or Linode instance—as a relic of the 2010s, a crude instrument for people who didn't understand the beauty of declarative state. But as I scaled my side projects and led small engineering teams, I noticed a recurring pattern. The more time I spent managing the "platform," the less time I spent shipping features. I had fallen into the trap of solving problems I didn't have, using tools designed for Google-scale traffic to serve a handful of early adopters.

The central metaphor of my mistake was the "Industrial Kitchen." Kubernetes is an industrial kitchen. It has walk-in freezers, commercial-grade ovens, and a dedicated staff for sanitation and inventory. If you are running a Michelin-star restaurant serving five hundred covers a night, you need that kitchen. But if you are just making a sandwich for yourself and a friend, trying to operate an industrial kitchen is a nightmare. You spend all your time cleaning the vents and calibrating the ovens instead of actually eating the sandwich. For a small project, you don't need an industrial kitchen; you just need a toaster and a knife.

## The Cognitive Tax of Over-Engineering

When you start a small project, your most valuable currency isn't money—it's cognitive load. Every single configuration file, every YAML indentation error, and every `kubectl` command is a tax on your mental bandwidth. In the early days of my Kubernetes obsession, I believed that the initial investment in complexity would pay dividends later. I told myself that "scaling would be easy." This is a lie we tell ourselves to justify playing with shiny toys. In reality, scaling a product that hasn't found product-market fit is a waste of time. 

I remember attempting to deploy a small project called "QuickSync," a niche data synchronization tool. I spent two days setting up Helm charts and configuring Horizontal Pod Autoscalers. I was thinking about what would happen if I hit 100,000 concurrent users. In reality, I had zero users. I was spending my cognitive budget on the "what if" instead of the "what is." The sheer volume of boilerplate required to get a basic app running in K8s is staggering. You need a Deployment, a Service, an Ingress, a ConfigMap, and a Secret just to get a "Hello World" to resolve to a domain name. Compare that to a simple systemd unit file on a VPS, and the disparity is offensive.

This overhead isn't just about the time spent writing YAML. It's the "invisible work." It's the time spent updating the cluster version because the managed provider is deprecating apiVersion v1beta1. It's the hour spent debugging why a pod is stuck in `ImagePullBackOff` because of a weird registry permission issue. It's the mental exhaustion of remembering whether a specific environment variable needs to be in a Secret or a ConfigMap. When you are a solo dev or a team of three, this overhead is a parasite that eats your productivity.

## The Cold, Hard Math of Infrastructure

Let's talk about the money, because this is where the "scaling" argument usually falls apart for projects under $50K ARR. Many developers assume that Kubernetes is "cheaper" because of bin-packing—the idea that you can squeeze many small apps onto one large node. While that's theoretically true, the operational reality is different.

Take a look at my old billing for a project I called "MetricFlow." I was using GKE (Google Kubernetes Engine). To have a stable cluster, I had three worker nodes to ensure high availability. Even with the smallest machine types, I was paying for the control plane (though Google offered some free tier credits) and three nodes running 24/7. My monthly bill was roughly $120. Now, look at the resource utilization. My pods were barely using 5% of the CPU and 10% of the RAM. I was paying for a massive amount of headroom that I never used. 

If I had moved MetricFlow to a single $12/month Hetzner or DigitalOcean VPS, I would have saved over $1,200 a year. For a project making $2,000 in annual revenue, that's a massive percentage of the margin. The "efficiency" of K8s only kicks in when you have enough services to actually fill those nodes. For a small project, you aren't bin-packing; you're just paying for empty space.

Here is a rough cost breakdown of the "K8s Tax" versus the "Simple Path" for a typical small project:

K8s Path: Managed Control Plane ($0-$70) + 3x Nodes ($60) + Load Balancer ($15) + Managed DB ($30) = ~$135 - $175 / month.
Simple Path: 1x High-RAM VPS ($20) + Managed DB ($30) = ~$50 / month.

That is a 60% to 70% reduction in cost for the exact same user experience. The user doesn't know if your app is running in a pod or on a bare Linux instance. They only care if the page loads in under two seconds. By choosing the complex path, I was essentially paying a "vanity tax" to feel like a "Cloud Native Engineer."

## The Incident That Broke My Spirit

The turning point for me wasn't the cost, but a catastrophic failure I call "The Great Ingress Meltdown." I had a small project—a specialized CRM for freelance designers—running on a cluster. I decided to update my Nginx Ingress Controller to a newer version. I followed the documentation. I tested it in a "dev" namespace. Everything seemed fine.

I pushed the change to production. Within ten minutes, the cluster started rejecting all traffic. Because I had misconfigured the annotations in my Ingress resource, the controller entered a crash loop. Because the controller was crashing, the health checks for the nodes started failing. Because the nodes were failing, the cluster autoscaler decided to terminate the "unhealthy" nodes and spin up new ones. This created a death spiral. The new nodes tried to pull the broken Ingress configuration, crashed, and were then terminated.

I spent six hours in a state of pure panic. I couldn't even `kubectl exec` into my pods because the API server was struggling to keep up with the churn of nodes joining and leaving the cluster. I was essentially locked out of my own house while the house was on fire. 

Contrast this with the failure mode of a simple VPS. If Nginx crashes on a VPS, you SSH in, you check the logs in `/var/log/nginx/error.log`, and you restart the service. It takes thirty seconds. In the K8s world, a simple configuration error can trigger a systemic failure that requires deep knowledge of the orchestration layer just to diagnose. I realized that I had traded "simple failures" (which are easy to fix) for "complex failures" (which are terrifying). I had built a system that was "resilient" to a single pod dying, but "fragile" to a configuration error. This is the paradox of Kubernetes: it solves for hardware failure but introduces a massive surface area for human configuration error.

## The "Industry Standard" Fallacy

I often hear people say, "But you should learn K8s because it's the industry standard." This is an argument for career development, not for project success. There is a profound difference between learning a tool for your resume and choosing a tool for your product. When you are building a project with the goal of making money or providing value, the only "standard" that matters is the one that allows you to ship the fastest with the fewest bugs.

I've read *The Mythical Man-Month* by Fred Brooks a dozen times, and its core lesson—that adding manpower to a late software project makes it later—applies here to complexity. Adding "enterprise-grade" infrastructure to a "startup-grade" project doesn't make it more professional; it makes it slower. I saw this happen at a mid-sized agency where I worked. We were tasked with building a MVP for a client. The lead architect insisted on a full EKS (Amazon Elastic Kubernetes Service) setup. We spent the first month on "infrastructure runway." The client was paying us for a product, and we were delivering "cluster stability reports." It was an embarrassing misalignment of goals.

Consider the philosophy in *The Pragmatic Programmer* by Andrew Hunt and David Thomas. They talk about the "tracer bullet" approach—getting a thin end-to-end slice of functionality working as quickly as possible. Kubernetes is the opposite of a tracer bullet. It's a heavy-duty armored vehicle. It's great if you're storming a beach, but it's useless if you're just trying to see if there's a path through the woods.

For those who insist on the "industry standard," I point to the success of companies like 37Signals. Jason Fried and David Heinemeier Hansson (DHH) have been vocal about their "Cloud Exit" strategy. They've moved away from the complexity of the cloud and back to owning their hardware and using simpler deployment patterns. If the people who built Basecamp and HEY think the current cloud-native trend is overblown, maybe it's time we stop pretending that K8s is the only way to run a professional app.

## Rethinking the Deployment Pipeline

When I finally decided to ditch Kubernetes for my small projects, I felt a sense of liberation. I moved back to a combination of Docker Compose and simple systemd scripts. I realized that 99% of what I wanted from K8s—automated restarts, easy environment variable management, and container isolation—could be achieved with far simpler tools.

Here is how my "Simplified Stack" looks compared to my "K8s Stack."

In the K8s world, I had a complex CI/CD pipeline using GitHub Actions that pushed images to GCR, updated a Helm chart, and performed a rolling update. It looked something like this:

```yaml
# Simplified snippet of a Helm-based deployment
- name: Deploy to GKE
  run: |
    helm upgrade --install my-app ./charts/my-app \
      --set image.tag=${{ github.sha }} \
      --namespace production
```

In my simplified world, I use a simple SSH-based deployment or a lightweight tool like Kamal (created by the 37Signals team). The deployment is essentially: pull the new image, stop the old container, start the new one.

```bash
# The "Simple Path" deployment logic
docker pull my-registry.com/app:latest
docker stop app_container
docker rm app_container
docker run -d --name app_container -p 80:80 --env-file .env my-registry.com/app:latest
```

Yes, there is a few seconds of downtime during the switch. But for a project with 50 users, a three-second gap once every two weeks is a negligible price to pay for the sanity of a 30-second deployment process. I no longer spend my weekends reading "K8s Networking" blogs. I spend my weekends actually coding features.

## Addressing the Counterarguments

Now, I know the "K8s Evangelists" are screaming. I can hear them now: "But what about scaling! What about zero-downtime deployments! What about service discovery!"

Let's address these honestly. First, the scaling argument. If your project grows to the point where a single large VPS cannot handle the load, you have a high-quality problem. At that point, you are likely making enough money to hire a dedicated DevOps engineer who can migrate you to K8s. The "scaling" problem is a luxury problem. If you are solving for 10 million users before you have 1,000, you are practicing "premature optimization," which Donald Knuth famously called the root of all evil.

Second, the zero-downtime argument. For a small project, "near-zero" downtime is sufficient. Using a simple blue-green deployment with two VPS instances and a load balancer in front of them provides 99.9% of the benefit of K8s rolling updates with 1% of the complexity. You don't need a complex orchestration layer to avoid a five-second blip during a deployment.

Third, the service discovery argument. In a small project, you usually have three or four services: a web app, a worker, a database, and a cache. You don't need a dynamic service mesh like Istio or Linkerd to find these. A simple `.env` file with the static IP of your database is more than enough. Using a service mesh for three services is like hiring a professional air traffic controller for a single paper airplane.

## The Path to Pragmatic Simplicity

If you are currently trapped in a cycle of managing a cluster for a project that doesn't justify it, my advice is to stop digging. The "sunk cost fallacy" is powerful in engineering. You feel that because you spent a month setting up your Prometheus/Grafana dashboards and your Calico networking, you *must* keep using the system. You don't.

The goal of a software engineer is not to use the most sophisticated tool; the goal is to solve the problem with the least amount of friction. For the vast majority of small projects, the "most sophisticated tool" is actually a hindrance.

I recently read *Working Backwards* by Colin Bryar and Jeff C comprehensive look at Amazon's internal processes. One of the key takeaways from the Amazon culture is the "Two-Pizza Team" rule—keeping teams small and autonomous. When you add a massive infrastructure layer like K8s, you effectively add a "ghost teammate" to your project. This ghost teammate demands constant attention, requires specific expertise, and frequently breaks things without warning. Why let a ghost run your project?

I have since migrated three of my active side projects off Kubernetes. The results were immediate. My infrastructure costs dropped by an average of 65%. My deployment time went from five minutes of "waiting for the pods to stabilize" to thirty seconds of "ssh and restart." Most importantly, my anxiety levels plummeted. I no longer wake up at 3 AM wondering if a rogue update has triggered a cascading failure in my cluster.

## Actionable Takeaways for the Over-Engineered

If you find yourself in the "Industrial Kitchen" trap, here are five specific recommendations to regain your sanity and your time.

First, apply the "Rule of 100." Until you have 100 paying customers or 10,000 active monthly users, you do not need a container orchestrator. Use a single VPS. If the app crashes, let it crash, and use a simple tool like Monit or systemd to restart it.

Second, prioritize "Boring Technology." Use Postgres instead of a fancy distributed NoSQL database. Use Nginx or Caddy instead of a complex ingress controller. Use a simple cron job instead of a complex Kubernetes Job schedule. Boring technology is reliable, well-documented, and doesn't require a certification to operate.

Third, separate your "Learning" from your "Earning." If you want to learn Kubernetes for your career, build a dedicated "K8s Lab" where you can break things and experiment. But do not use your profit-generating projects as the laboratory. The cost of a production outage is too high a price for a learning experience.

Fourth, embrace "Manual Scaling" for longer than you think. You can scale a VPS vertically (adding more RAM and CPU) with a single click in a dashboard. This "vertical scaling" can carry you surprisingly far—often all the way to several thousand concurrent users—before you ever need the "horizontal scaling" that K8s provides.

Finally, audit your "Infrastructure-to-Feature Ratio." If you spend more than 20% of your development time on CI/CD pipelines, cluster maintenance, and YAML tweaking, you are over-engineered. Strip it back. Delete the Helm charts. Kill the pods. Go back to the basics.

The journey from Kubernetes enthusiast to pragmatic minimalist was a humbling experience for me. It required me to admit that I was using complexity as a proxy for quality. But in the end, the most "professional" thing I could do for my projects was to make them simple. Because at the end of the day, the only thing that matters is whether the software works and whether the business is viable. Everything else is just noise. Stop building the space shuttle; just buy a bicycle and start pedaling.