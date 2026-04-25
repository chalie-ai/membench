# How I Accidentally Built a Distributed System

I remember the exact moment my soul left my body. It was a Tuesday at 3:14 AM, and I was staring at a Grafana dashboard that looked like a heart attack in neon green. I was the Lead Engineer at a mid-sized fintech startup—let’s call it "WealthFlow"—and we had just hit 100,000 concurrent users during a market volatility event. Our "simple" Ruby on Rails monolith, which I had spent eighteen months polishing into a shiny piece of engineering, wasn't just crashing; it was actively fighting back.

The system had entered a state of recursive failure. The database was locking, the cache was poisoning itself, and the background workers were eating each other in a desperate bid for memory. I had spent the last year "optimizing" the app, and in doing so, I had unwittingly constructed a distributed system without ever reading a book on distributed systems. I had built a Rube Goldberg machine of dependencies, and I was the only one who knew where the strings were tied.

To understand how this happened, you have to understand the Great Architectural Lie. The lie is that you can solve performance problems by adding "small pieces" of infrastructure. We tell ourselves that adding a Redis cache is just a "tweak," or that moving a heavy report generation to a Sidekiq queue is just "best practice." But infrastructure is like a house of cards; every new component you add isn't just a feature, it's a new failure mode. I didn't build a distributed system on purpose. I drifted into it, one "small tweak" at a time, until I woke up in a nightmare of eventual consistency and network partitions.

## The Illusion of the Monolith

In the beginning, WealthFlow was a beautiful, boring monolith. We had a single PostgreSQL database and a fleet of three EC2 instances running Puma. It was predictable. If the app crashed, we restarted the process. If the DB was slow, we added an index. It was a synchronous world; a request came in, the code did some work, and a response went out. This is the "Goldilocks Zone" of software engineering, where the mental model of the code matches the physical reality of the hardware.

The trouble started when we hit about 10,000 active users. Suddenly, the "simple" dashboard page took four seconds to load. My instinct—and the instinct of every engineer who has ever read a Medium article on scaling—was to introduce caching. I implemented Redis for session storage and fragment caching. At the time, it felt like a victory. Our response times dropped by 60%, and I felt like a god of performance.

But this was the first brick in the wall. By introducing Redis, I had transitioned from a single-process system to a distributed one. I now had two different types of state: the durable state in Postgres and the volatile state in Redis. I had introduced the "Dual Write" problem. If the Postgres transaction succeeded but the Redis update failed, the user saw old data. I brushed this off as a "rare edge case." I told my team that the 0.1% inconsistency didn't matter. This was my first great sin: believing that distributed state is just "local state with a network cable."

## The Queue of Doom

As we grew to a team of 12 engineers, the "small tweaks" accelerated. We needed to send emails, process CSV uploads, and sync with Plaid for banking data. We couldn't do this in the request-response cycle, so we introduced Sidekiq. This felt like the right move. We were following the "industry standard" approach. We moved the heavy lifting to background workers, effectively decoupling the user experience from the processing time.

Here is a snippet of the logic we used for our transaction processing:

```ruby
def process_transaction(transaction_id)
  transaction = Transaction.find(transaction_id)
  if transaction.pending?
    # Update DB
    transaction.update!(status: 'processing')
    # Trigger external API call via queue
    PaymentGatewayWorker.perform_async(transaction.id)
    # Update cache to hide latency
    Rails.cache.write("tx_#{transaction.id}", 'processing')
  end
end
```

On paper, this is clean. In reality, it was a disaster waiting to happen. By moving logic into an asynchronous queue, I had surrendered the luxury of the ACID transaction. I was now dealing with "at-least-once delivery." Because Sidekiq guarantees that a job will be executed *at least* once, we started seeing duplicate payments. A network hiccup would cause a worker to timeout, Sidekiq would retry the job, and the customer would be charged twice.

I tried to fix this by implementing idempotency keys, but because I didn't actually understand the CAP theorem, I implemented them using the same Redis cache I was using for session storage. I had created a circular dependency where the reliability of my payment system depended on the availability of a non-persistent cache. I was no longer writing a web app; I was managing a choreography of disparate systems that had no shared sense of time or truth.

## The Microservice Mirage

By the time we hit 50,000 users, the monolith was feeling "heavy." The deployment pipeline took twenty minutes, and developers were stepping on each other's toes in the `User` model. My CTO, who had recently attended a conference where a Netflix engineer talked about microservices, suggested we "break out the billing logic" into its own service.

We spent three months building "BillingService," a separate Go application. We felt sophisticated. We were using gRPC for communication and Prometheus for monitoring. We thought we were maturing. In reality, we were just adding network latency to our most critical path. 

The "BillingService" was now a separate entity with its own database. Now, when a user updated their credit card, we had to update the Monolith and the BillingService. I tried to handle this with a distributed transaction—a "Saga pattern" I'd read about in a blog post. But I didn't have a coordinator; I just had the Monolith sending HTTP requests to the BillingService and hoping for the best.

```yaml
# Our "sophisticated" gRPC timeout config
grpc_settings:
  timeout: 5s
  retries: 3
  backoff:
    initial: 100ms
    max: 2s
```

This configuration looked professional, but it was a death trap. When the BillingService slowed down due to a database lock, the Monolith's request threads would hang for 5 seconds. Because we had 3 retries, a single failing request could hold a thread for 15 seconds. With a fleet of 20 servers, we quickly exhausted our connection pools. We had created a "cascading failure," where a slowdown in a downstream service caused a total blackout of the upstream service. This is the classic "death spiral" described in Martin Kleppmann’s *Designing Data-Intensive Applications*. I had ignored the warnings and built a system where failure was contagious.

## The Great Tuesday Meltdown

This brings us back to that Tuesday at 3:14 AM. The market volatility had triggered a surge in activity. Users were refreshing their dashboards every few seconds. Our Redis cache, which I had scaled to 64GB, hit a memory limit and started evicting keys. 

Because the cache was gone, every single request hit the Postgres database. The database, overwhelmed by the sudden 10x spike in load, slowed down. This triggered the gRPC timeouts I had configured for the BillingService. The Monolith began retrying requests, which further hammered the BillingService, which in turn put more pressure on the database.

Then, the "final boss" appeared: the Sidekiq queue. Because the database was slow, the workers couldn't complete their jobs. The queue grew from 10,000 to 2 million jobs. These jobs were consuming all available RAM on the worker nodes. The Linux OOM (Out of Memory) killer started terminating processes randomly.

I remember the feeling of utter helplessness. I tried to scale the database, but the "thundering herd" of 2 million queued jobs hit the new instance the second it came online, crashing it instantly. I was in a state of "metaspace failure"—the tools I used to fix the system were themselves failing because they depended on the system I was trying to fix. 

I spent the next six hours manually purging the Redis cache and flushing the Sidekiq queues. I essentially deleted a day's worth of transaction logs to save the company from total collapse. We lost approximately $42,000 in missed processing fees and suffered a 15% churn rate of new users who had signed up that morning and found the site dead.

## The Philosophical Pivot

After the dust settled, I spent two weeks reading. I didn't read "how-to" guides; I read the foundational texts. I read Leslie Lamport’s papers on logical clocks. I watched the original talks on the Raft consensus algorithm. I realized that I had treated my system as a collection of components, whereas a distributed system is actually a collection of *failures*.

The mistake I made was treating the network as a reliable cable. In my head, a call to `BillingService.update()` was the same as calling a method on a local object. But the network is not a cable; it is a chaotic, probabilistic medium. When you move a function call across a network boundary, you are no longer writing code; you are managing a negotiation.

I also had to confront the "Microservices Ego." We had moved to a distributed architecture not because our domain required it, but because we wanted to feel like we were at Google. We had traded "code complexity" (which is easy to debug with a debugger) for "operational complexity" (which requires a PhD in observability to understand).

Some might argue that my approach was simply "under-engineered." They would say that if I had used a service mesh like Istio or a more robust orchestrator like Kubernetes from the start, the cascading failures would have been mitigated by circuit breakers. To that, I say: fuck your service mesh. Adding a complex service mesh to a system you don't understand is like putting a professional racing steering wheel on a car that has no brakes. It doesn't solve the problem; it just gives you more buttons to press while you're crashing.

Others might argue that the monolith was doomed anyway and that the "distributed" part was inevitable. This is a half-truth. Scaling is inevitable, but *distribution* is a choice. You can scale vertically for a surprisingly long time. We could have moved to a larger Aurora instance and kept our logic in one place for another year. Distribution is a tool for solving specific problems—like geographic latency or organizational scaling—not a prerequisite for "growth."

## The Path to Sanity

We spent the next six months "de-distributing" our system. We didn't go back to a simple monolith—that's impossible once you've tasted the cloud—but we moved toward a "Modular Monolith" approach. We merged the BillingService back into the main codebase, but kept the logic separated by strict internal boundaries.

We replaced our fragile gRPC calls with a robust event-driven architecture using Apache Kafka. Instead of the Monolith *telling* the BillingService to do something and waiting for a response, the Monolith now emitted an event: `TransactionCreated`. The billing logic listened to that event and processed it at its own pace. This decoupled the availability of the two systems. If the billing logic crashed, the users could still use the app; the billing would simply catch up once the service recovered.

Here is how our event schema looked, emphasizing versioning to avoid the "poison pill" problem:

```json
{
  "event_id": "uuid-12345",
  "event_type": "transaction.created",
  "version": "1.2.0",
  "payload": {
    "transaction_id": "tx_999",
    "amount": 1500,
    "currency": "USD"
  },
  "timestamp": "2023-10-27T10:00:00Z"
}
```

By introducing a durable log (Kafka), we solved the idempotency problem. We no longer relied on Redis to remember if we had processed a payment; we relied on the offset of the Kafka partition. We moved from a world of "hope-based consistency" to a world of "guaranteed eventual consistency."

## Hard-Won Takeaways

If you are currently in the process of adding "just one more tool" to your stack, please stop and read this. You are not just adding a feature; you are adding a new way for your system to die.

First, assume the network is a liar. Every single time you make a network call, assume that it will fail, that it will hang, or that it will return a successful response but the data will be corrupted. Implement timeouts, retries with exponential backoff, and circuit breakers—not as "extra" features, but as the primary logic of your integration.

Second, prioritize "Observability" over "Monitoring." Monitoring is telling you that the system is down. Observability is telling you *why* it is down. Don't just track CPU and RAM; track "request lineage." Use tools like OpenTelemetry to trace a single request as it travels through your system. If you can't see the path a request took across your services, you are flying blind in a storm.

Third, beware the "Distributed Transaction" trap. If you find yourself trying to coordinate a state change across two different databases, you have already lost. Either merge the databases or embrace eventual consistency. Use a transactional outbox pattern to ensure that your database updates and your event emissions happen atomically.

Fourth, resist the urge to decompose your monolith until the pain of the monolith is greater than the pain of the network. Microservices are an organizational tool for managing 500 developers; they are a tax on a team of 15. If your team can fit in a single medium-sized room, you probably don't need a distributed architecture.

Fifth, read the classics. Stop reading "Top 10 Frameworks for 2024" and go read *Designing Data-Intensive Applications* by Martin Kleppmann. Read *Site Reliability Engineering* by the Google team. Understand the fundamentals of consensus, replication, and partitioning. The tools change every six months, but the physics of distributed systems—the trade-offs between consistency and availability—have not changed since the 1980s.

Building a distributed system by accident is a rite of passage for many of us. It is a humbling, terrifying, and expensive experience. But once you've seen your system collapse under its own weight, you stop chasing "scale" and start chasing "reliability." Because at the end of the day, the fastest system in the world is useless if it's currently in a death spiral at 3:14 AM.