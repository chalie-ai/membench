# What I Learned Interviewing 200 Senior Engineers

I remember sitting in a glass-walled conference room at a mid-sized fintech firm about four years ago, staring at a candidate who was, on paper, a god. He had a decade of experience at Google, a contributing record to the Linux kernel, and a resume that looked like a curated list of every buzzword from the 2015-2020 era. I gave him a standard medium-hard LeetCode problem involving a priority queue. He solved it in six minutes. He didn't even break a sweat. He optimized the time complexity to $O(n \log k)$ and then spent ten minutes explaining why the specific cache-line alignment of the data structure mattered for performance on ARM architectures.

I hired him on the spot. I felt like a genius for finding a "10x engineer." Six months later, that same engineer had caused a production outage that cost the company roughly $45,000 in lost transaction fees because he decided to rewrite a stable, boring piece of the payment gateway in a custom concurrency primitive he’d designed over a weekend. He couldn’t collaborate with the junior devs, he viewed code reviews as a personal insult, and he spent more time arguing about the philosophical purity of functional programming than he did shipping features. He was a technical virtuoso and a professional liability.

That was my wake-up call. Over the next three years, as I moved into a technical leadership role, I conducted approximately 200 interviews for senior and staff-level positions. I’ve seen the heights of brilliance and the depths of "resume padding." I’ve spent thousands of hours listening to people explain how they scaled systems to millions of users, only to realize they were the third person on a team of fifty and had mostly just updated the README files. 

If we treat the technical interview as a map, most of us are trying to navigate a city using a map of a completely different city. We are measuring "interviewing skill," not "engineering skill." To use a metaphor that will haunt this entire piece: the modern technical interview is not a diagnostic test; it is a high-stakes piece of theater. The candidate is the actor, the interviewer is the audience, and the "coding challenge" is merely the prop. The problem is that we are hiring the best actors, not the best engineers.

## The Theater of the Whiteboard

For years, the industry has been obsessed with the "signal." We want a binary signal—Yes or No—that tells us if someone can handle the complexity of a distributed system or a massive codebase. But the signal we get from a 45-minute coding exercise is almost entirely noise. When I ask a senior engineer to invert a binary tree on a whiteboard, I am not testing their ability to architect a scalable API; I am testing their ability to remember a specific academic exercise from six years ago while a stranger watches them sweat.

Most senior engineers don't spend their days solving algorithmic puzzles in a vacuum. They spend their days reading old, shitty code written by people who left the company three years ago, navigating the politics of a product roadmap, and trying to figure out why a Kubernetes pod is crashing in a way that defies the laws of physics. None of that is captured by a LeetCode Medium.

I remember interviewing a candidate for a Lead Role who struggled with a basic dynamic programming question. He was stumbling, hesitating, and eventually failed to find the optimal solution. But as we talked about his previous work at a company like Stripe, he described in vivid detail how he’d migrated a legacy monolithic database to a sharded architecture without a second of downtime. He talked about the trade-offs, the failures, and the human elements of that migration. He had the "scar tissue" of a real veteran. Yet, according to the "rubric" of the theater, he was a "No." We almost let a world-class engineer walk out the door because he couldn't remember the exact syntax for a recursive memoization pattern.

## The Archetypes of the Senior Candidate

After 200 interviews, I realized that candidates generally fall into four archetypes. Recognizing these early saves hours of wasted time and prevents the "Virtuoso Disaster" I mentioned earlier.

First, there is the Academic. This person is a master of the theater. They can solve any puzzle you throw at them, and their code is syntactically perfect. However, they often struggle with the "boring" parts of engineering. They want to use the most complex tool for the simplest job. If you ask them to build a simple CRUD app, they’ll suggest a distributed actor model with Event Sourcing and a CQRS pattern because it's "more correct," even though the project only has ten users.

Second is the Careerist. This person knows exactly what you want to hear. They use the right keywords—"scalability," "observability," "idempotency"—but when you dig into the *why*, the answers are shallow. They can tell you that they used Kafka for a messaging queue, but they can't tell you why they chose Kafka over RabbitMQ or how they handled partition rebalancing. They have a broad but thin layer of knowledge, polished to a mirror shine for the interview process.

Third is the Burnout. These are often the most talented engineers, but they’ve been chewed up and spit out by the "big tech" machine. They are cynical and tired. They will tell you exactly why your current architecture is garbage within ten minutes of the call. The risk here is cultural; the reward is that they have seen every possible way a system can fail and can prevent those failures from happening to you.

Finally, there is the Craftsman. This is the gold standard. The Craftsman isn't necessarily the fastest coder in the room, but they are the most thoughtful. They ask about the business constraints. They ask who the end-user is. When they write code, they write it for the person who has to maintain it in two years. They treat the codebase like a garden, not a monument to their own intelligence.

## The Signals That Actually Predict Success

If the theater of the whiteboard is useless, what actually works? I spent a year iterating on my interview process, moving away from puzzles and toward "systemic storytelling." I stopped caring about whether they could optimize a sorting algorithm and started caring about how they handle ambiguity.

The strongest signal I’ve found is the "Decision Log." I ask candidates to describe a technical decision they made in the last year that they now regret. If a candidate says they’ve never made a mistake or that their only mistake was "working too hard," I immediately mark them as a risk. True senior engineers are defined by their mistakes. I want to hear about the time they pushed a breaking change to production on a Friday afternoon and had to spend Saturday rolling back 400 microservices.

I want to hear a narrative like: "We chose MongoDB because of the flexible schema, but as the dataset grew to 50TB, we hit a wall with consistency. I spent three months designing a migration to PostgreSQL, and here is how we handled the data transformation without losing a single record." That is a signal. That is a person who understands the cost of technical debt.

Another high-signal approach is the "Code Review Simulation." Instead of asking them to write code from scratch, I give them a piece of intentionally flawed code—something that looks okay at first glance but has a subtle race condition or a massive memory leak. 

For example, I might show them a Go snippet like this:

```go
func processData(items []string) {
    var wg sync.WaitGroup
    for _, item := range items {
        wg.Add(1)
        go func() {
            fmt.Println(item) // The classic loop variable capture bug
            wg.Done()
        }()
    }
    wg.Wait()
}
```

A junior will say the code looks fine. A "Theater" candidate might notice the `sync.WaitGroup` is correct. A true Senior Engineer will immediately point out that `item` is being captured by reference in the closure, leading to a race condition where most of the output will be the final element of the slice. That is a real-world signal. It tells me they have spent time debugging concurrency in production.

## The Great Technical Lie: "The Right Tool for the Job"

We love to talk about using the "right tool for the job," but in 200 interviews, I discovered that most people use "the tool I'm most comfortable with" and then rationalize it as the "right tool." This is where the theater becomes dangerous. We hire people who are experts in a specific stack—say, React and Node.js—and we assume that expertise translates to senior engineering ability.

It doesn't. Tooling is cheap; thinking is expensive. I’ve interviewed people who could recite the entire React lifecycle by heart but couldn't explain the basics of a CAP theorem trade-off. They were "Senior React Developers," but they weren't "Senior Engineers."

The difference is that a Senior Engineer understands that the tool is a means to an end. If I'm building a system to track a few hundred internal assets, I don't need a distributed NoSQL cluster. A single SQLite file on a reliable disk is often the "right tool." 

I once interviewed a candidate who insisted that every project should use Kubernetes. He had a certification for it, he loved the ecosystem, and he spoke about it with religious fervor. But when I asked how he would deploy a simple landing page for a marketing site, he still suggested a multi-region K8s cluster with an Istio service mesh. He wasn't solving a problem; he was applying a pattern he had learned. He was a victim of the "Golden Hammer" fallacy—to a man with a hammer, everything looks like a nail. In this case, the hammer was a $2,000-a-month cloud bill and a massive operational overhead that the project didn't justify.

## The Failure: When I Hired the Mirror

I have to be honest about my own failures. Early in my leadership journey, I fell into the trap of "culture fit," which is often just a polite way of saying "I want to hire people who think like me." I once hired a developer because we both loved the same obscure Rust crates and shared a mutual disdain for Java's verbosity. We clicked. The interview felt effortless. We spent an hour talking about the beauty of ownership and borrowing instead of digging into his actual architectural experience.

It was a disaster. Because we were so similar in our technical biases, we created a massive blind spot in the team. When we hit a wall with our database performance, neither of us wanted to admit that we needed a traditional relational model; we kept trying to force our "modern" approach to work. We spent three months fighting the tools instead of solving the business problem.

I learned that "culture fit" is a lie. You don't want a mirror; you want a puzzle piece. You want someone who challenges your assumptions, who asks "Why are we doing it this way?" and who isn't afraid to tell you that your favorite library is overkill for the task at hand. The best teams aren't made of people who agree; they are made of people who can disagree productively.

## Addressing the Counter-Arguments

Now, some will argue that my critique of the "theater" is too harsh. They will say that algorithmic challenges are a necessary filter. The argument is that if you can't solve a Linked List problem, you lack the fundamental cognitive ability to handle complex systems. This is the "IQ test" theory of interviewing, championed by companies like Google and Meta.

To this, I say: perhaps for a PhD in Computer Science entering a research role, that's true. But for a Senior Engineer tasked with delivering business value? It's a faulty correlation. I know dozens of engineers who struggle with the "Two Sum" problem but can lead a team of twenty through a legacy migration of a core banking system. The ability to manipulate a pointer in a whiteboard environment is not a proxy for the ability to manage technical debt over a five-year horizon.

Another counter-argument is that "Standardized Interviews" ensure fairness. By giving everyone the same LeetCode test, you remove bias. While that sounds good in theory, it actually introduces a different kind of bias: it favors those who have the time and resources to "grind" LeetCode. It favors the person who spent three months studying "Patterns of Dynamic Programming" over the person who spent those three months building a real open-source project or mentoring junior developers. We aren't measuring talent; we are measuring the ability to prepare for a specific, artificial test.

## The Path Forward: A New Framework for Hiring

If we stop the theater, what do we do? After 200 interviews and several high-profile hiring mistakes, I’ve landed on a framework that focuses on evidence over performance.

First, stop the "Puzzle" phase. Replace it with a "System Design Review" of a real project the candidate has worked on. Don't ask them to design "Twitter" or "Uber"—those are just as theatrical as LeetCode. Ask them to walk you through a project they actually shipped. Ask them where the bottlenecks were. Ask them what they would change if they had to do it again today.

Second, implement a "Pair Programming" session on a real-world task. Give them a small, existing codebase with a bug. Let them use their IDE, let them use Google, and let them use Stack Overflow. That is how engineering is actually done. I want to see how they navigate a folder structure, how they use a debugger, and how they communicate their thought process as they struggle.

Third, prioritize "Operational Empathy." Ask them how they feel about on-call rotations. Ask them how they handle a production incident. A senior engineer who thinks "the ops team handles that" is not a senior engineer; they are a developer who happens to have a high tenure.

To wrap this up, if you are a hiring manager or a lead, stop looking for the "perfect" candidate. There is no such thing. There is only the candidate whose strengths align with your current gaps and whose failures you are equipped to manage.

Here are my final, actionable takeaways for anyone looking to hire (or be hired) as a senior engineer:

1. Kill the LeetCode puzzles. They measure "test-taking ability," not "engineering ability." Replace them with a a "Real-World Debugging" session where the candidate fixes a bug in a medium-sized, existing codebase.

2. Hunt for "Scar Tissue." Prioritize candidates who can give a detailed, humble account of a major technical failure and what they learned from it. A candidate with no failures is a candidate who hasn't taken enough risks or hasn't been paying attention.

3. Test for "Boringness." The best senior engineers are the ones who are comfortable with boring technology. If they insist on the "newest, shiniest" tool regardless of the scale of the problem, they will cost you more in maintenance than they will provide in performance.

4. Hire for "Cognitive Diversity." Stop looking for "culture fit" and start looking for "culture add." Find the person who thinks differently than you do, provided they can communicate those differences clearly and respectfully.

5. Read "The Mythical Man-Month" by Fred Brooks, "Working Effectively with Legacy Code" by Michael Feathers, and "Designing Data-Intensive Applications" by Martin Kleppmann. These three books provide a far better framework for what "Seniority" actually means than any interview rubric ever will.

Engineering is not a performance; it is a practice. It is the slow, often tedious process of reducing complexity and managing uncertainty. The next time you step into an interview—whether as the actor or the audience—remember that the goal is not to put on a great show. The goal is to find someone who can actually build the thing.