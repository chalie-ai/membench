# How I Migrated 2TB of Production Data with Zero Downtime

I remember the exact moment I realized we were fucked. It was 3:14 AM on a Tuesday in October, and I was staring at a Grafana dashboard that looked like a crime scene. Our primary PostgreSQL instance—a massive, monolithic beast we’d spent four years nursing—was hitting 98% CPU utilization. We were a fintech platform handling thousands of transactions per second, and our "scale-up" strategy had finally hit a physical wall. We had thrown every amount of RAM and NVMe storage at the problem, but the vacuuming process was taking longer than the day itself. We weren't just slowing down; we were flirting with a catastrophic outage that would have cost the company roughly $45,000 per minute in lost transaction fees.

For the uninitiated, migrating a production database is like trying to replace the engines of a Boeing 747 while it’s cruising at 30,000 feet with four hundred nervous passengers on board. You can't just "turn it off" for a weekend. In the world of high-frequency finance, a four-hour window of downtime isn't a "maintenance break"—it's a corporate suicide note. I spent the next six months obsessing over how to move 2 terabytes of mission-critical ledger data from Postgres to CockroachDB without a single millisecond of unavailability.

The guiding metaphor for this entire odyssey was the "Bridge Construction" strategy. You don't blow up the old bridge and hope the new one is ready; you build a second bridge parallel to the first, divert a tiny amount of traffic, test the structural integrity, and slowly shift the load until the old bridge is empty and can be demolished.

## The Architectural Wall and the Choice of CockroachDB

Our team of twelve engineers had spent years optimizing Postgres, but we were fighting a losing battle against the laws of physics. We needed horizontal scalability and global distribution because we were expanding into the EU market. We looked at Spanner, but the GCP lock-in felt too restrictive. We looked at TiDB, but the ecosystem didn't feel as mature for our specific compliance needs. We landed on CockroachDB because it promised the familiarity of the Postgres wire protocol with the distributed nature of a Google-style Spanner architecture.

The transition wasn't a slam dunk. Postgres is a master of flexibility; CockroachDB is a master of scale. However, the "distributed" part of the equation introduces a new demon: latency. In a monolithic Postgres setup, a join is a local memory operation. In a distributed system, a poorly written join can trigger a "network storm" where nodes spend more time talking to each other than actually processing data. I remember reading *Designing Data-Intensive Applications* by Martin Kleppmann, and his sections on consistency and replication hit me like a ton of bricks. I realized that if we just "lifted and shifted" our schema, we would essentially be building a very expensive, very slow version of the database we already had.

We spent three weeks just auditing our indexes. We discovered that several of our most frequent queries relied on sequential primary keys, which in a distributed database creates "hot spots." If every single transaction hits the same range of keys, you aren't distributing the load—you're just creating a bottleneck in a different zip code. We had to migrate from `SERIAL` integers to `UUIDs` across several trillion-row tables, a task that felt like trying to repaint a house while the paint was still wet.

## The Dual-Write Strategy: Building the Second Bridge

The core of the zero-downtime migration is the dual-write pattern. You cannot simply export a dump and import it; by the time the 2TB import finishes, your data is already stale. Instead, we implemented a sophisticated middleware layer using Kafka and a custom Go service we dubbed "The Synchronizer."

The logic followed a strict sequence. First, we modified our application code to write to both PostgreSQL and CockroachDB. Crucially, the Postgres write remained the "source of truth." If the write to CockroachDB failed, we logged the error and moved on. We didn't let the new system crash the old one. This phase lasted for two weeks. We weren't migrating old data yet; we were simply ensuring that all *new* data was landing in both places.

```go
func SaveTransaction(tx Transaction) error {
    // Primary write to legacy Postgres
    err := postgresDB.Save(tx)
    if err != nil {
        return err // Hard failure if the source of truth fails
    }

    // Asynchronous shadow write to CockroachDB
    go func() {
        err := cockroachDB.Save(tx)
        if err != nil {
            log.Errorf("Shadow write failed for tx %s: %v", tx.ID, err)
            // Push to a dead-letter queue for later reconciliation
            kafkaDLQ.Push(tx)
        }
    }()
    
    return nil
}
```

While the dual-writes were capturing the "now," we had to handle the "then." We used a modified version of an open-source tool called `pg_dump` combined with a custom batching script to migrate the historical 2TB of data in chunks. We moved the data in reverse chronological order, starting from the most recent and working backward. This allowed us to verify the most relevant data first. The real nightmare was the "collision window"—the period where the batch migration of old data overlapped with the real-time dual-writes. We solved this by using "upsert" logic in CockroachDB, ensuring that the real-time write always won over the historical import.

## Shadow Testing and the Art of Paranoia

Once the data was flowing into both systems, we entered the "Shadow Testing" phase. This is where most engineers get lazy. They assume that because the data is there, it's correct. I’ve been burned before—specifically back in 2016 during a botched migration at a previous startup where I assumed a `TIMESTAMP` conversion was seamless, only to realize I’d shifted every single user's birthday by exactly six hours. That failure cost us a weekend of frantic patching and a very angry CEO. I vowed never to trust a migration without a bit-for-bit comparison.

We implemented a "Comparison Proxy." For every read request coming into the API, the proxy would send the query to both Postgres and CockroachDB. It would then compare the results. If the results matched, the proxy returned the Postgres result to the user. If they differed, it logged a "diff" to an Elasticsearch cluster for us to analyze.

The results were humbling. In the first 48 hours, we found a 0.4% discrepancy rate. It turned out that CockroachDB’s handling of certain `NULL` values in complex joins differed slightly from Postgres. We also found that our query performance on the new system was actually 15% slower for a specific set of ledger reports. We spent a week iterating on the indexes, eventually implementing "interleaved tables" to keep related data physically close on the disk, which brought the latency down to a crisp 12ms.

## The 72-Hour Cutover Weekend

The cutover is the moment of maximum peril. We scheduled it for a Friday evening, giving us a three-day window to roll back if everything went to hell. Our plan was not a "big bang" switch but a graduated migration of traffic based on user segments.

On Friday at 8:00 PM, we shifted 1% of our users to use CockroachDB as the source of truth. For these users, the writes went to CockroachDB first, and then were asynchronously replicated back to Postgres. This "reverse dual-write" was our insurance policy. If we detected a bug in the new system, we could flip the switch back to Postgres without losing a single transaction from that 1% of users.

By Saturday morning, we were at 10% traffic. We monitored the "p99" latency and the error rates like hawks. We noticed a spike in CPU on one specific CockroachDB node—a "hot range" issue where a single account with millions of transactions was overwhelming one node. We quickly used the `SPLIT RANGE` command to distribute that account's data across the cluster. If we had been at 100% traffic, that node would have crashed, triggering a cascading failure across the cluster.

By Sunday afternoon, we hit 100%. The feeling of flipping that final switch was a mix of euphoria and absolute terror. We stayed on high alert for 48 hours, watching the logs for any sign of "ghost" data or consistency errors. We had successfully moved 2TB of data and transitioned our entire user base with zero seconds of scheduled downtime.

## Addressing the Skeptics: Is Distributed Always Better?

Now, I want to be honest. There are two major counterarguments to the "Distributed is Better" thesis that I encountered during this process. First, the "Complexity Tax." Some of my senior architects argued that we were trading a scaling problem for a complexity problem. They weren't wrong. Managing a distributed cluster requires a different mental model. You can no longer assume that `ORDER BY` is cheap, and you have to be hyper-aware of network topology. If you don't have a team capable of managing the operational overhead, a distributed DB is just a fancy way to fail at scale.

Second, there is the "Latency Trade-off." In a single-node Postgres instance, the speed of light isn't an issue. In a distributed system, the consensus protocol (Raft, in the case of CockroachDB) requires a majority of nodes to agree on a write. This introduces a floor to your latency. For some ultra-low-latency applications, this is a deal-breaker. We accepted this trade-off because our bottleneck wasn't the latency of a single write, but the throughput of the entire system. We traded 2ms of local latency for the ability to handle 10x the total volume of transactions.

## Actionable Takeaways for the Bold

If you find yourself staring at a monolithic database that is beginning to buckle under its own weight, do not panic, but do not be complacent. This migration taught me that the technical challenges are actually the easy part; the hard part is the risk management. Here are my five non-negotiable recommendations for anyone attempting a high-stakes data migration.

First, never trust your migration scripts. Always build a comparison proxy that validates the output of the new system against the old system in real-time. If you aren't comparing millions of rows of production data in a shadow environment, you are just guessing.

Second, implement a reverse dual-write path. The ability to move back to the old system without data loss is the only thing that will allow you to sleep during the cutover weekend. Your rollback plan should be as detailed as your rollout plan.

Third, audit your primary keys. Moving to a distributed database while keeping sequential integers is like buying a Ferrari and then refusing to take it out of first gear. Use UUIDs or hash-sharded indexes to avoid hot spots.

Fourth, read the literature. I cannot stress enough how much *Designing Data-Intensive Applications* by Martin Kleppmann and the "CAP Theorem" paper by Eric Brewer helped us avoid catastrophic architectural mistakes. Understanding the trade-offs between consistency and availability is the difference between a successful migration and a deleted production table.

Fifth, automate your reconciliation. You will have data gaps. You will have dropped packets. You will have "zombie" records. Build a tool that can scan both databases and identify discrepancies automatically so your engineers don't spend their weekends manually querying SQL.