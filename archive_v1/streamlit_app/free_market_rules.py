"""
Tuttle Twins - Free Market Rules: the Grade 5 economics course.

WHY THIS FILE EXISTS
--------------------
Thirty units of four lessons each, extracted from the publisher PDFs
("Free Market Rules: Economics Curriculum (All 30 Units)", split 1-10 / 11-20 /
21-30). Unit and lesson titles are verbatim from each PDF's table of contents,
so the wording here matches what Sonny sees on the page. Ligatures and curly
quotes from the PDF text layer were normalised; nothing else was reworded.

Lesson 4 of every unit is the applied one -- the publisher closes each unit by
turning the concept on the student ("How do YOU use resources around you?",
"What do YOU want money to be?"). Those are typed as `project` rather than
`lesson` so they read as something to do rather than something to read.

WHERE IT SITS IN THE WEEK
-------------------------
One lesson per core day, Mon-Thu, running alongside math. It took over the
Tuesday and Thursday slots Brilliant.org used to hold, which is what keeps the
daily ceiling at five assignments instead of pushing it to six.
"""

LESSON_MINUTES = 20
LESSON_XP = 10
CATEGORY = "Economics (Free Market Rules)"

# (unit number, unit title, [(lesson number, lesson title), ...])
UNITS = [
    (1, "Unit 1: Wants & Needs", [
        (1, 'What are wants and needs?'),
        (2, 'How do wants and needs change?'),
        (3, 'What do we need to satisfy our wants?'),
        (4, 'What do you want?'),
    ]),
    (2, "Unit 2: Resources", [
        (1, 'What are resources?'),
        (2, 'When does something become a resource?'),
        (3, 'How do people use resources?'),
        (4, 'How do you use resources around you?'),
    ]),
    (3, "Unit 3: Scarcity", [
        (1, 'What is scarcity?'),
        (2, 'Which things are actually scarce?'),
        (3, 'How do people deal with scarcity?'),
        (4, 'How does scarcity affect you?'),
    ]),
    (4, "Unit 4: Choices & Trade-offs", [
        (1, 'How do you choose?'),
        (2, "What do a person's choices show us?"),
        (3, "What's the cost of a trade-off?"),
        (4, 'How can you make better choices?'),
    ]),
    (5, "Unit 5: Incentives", [
        (1, 'What gets you out of bed?'),
        (2, 'Do incentives change?'),
        (3, 'Do actions speak louder than words?'),
        (4, 'Is your skin in the game?'),
    ]),
    (6, "Unit 6: Value", [
        (1, 'What makes something valuable?'),
        (2, 'How did people think of theories of value?'),
        (3, 'How is value created?'),
        (4, 'How can you create value?'),
    ]),
    (7, "Unit 7: Production & Consumption", [
        (1, 'How does value flow?'),
        (2, 'How are consumption and production related?'),
        (3, 'Where do we see production and consumption in the real world?'),
        (4, 'Are you a producer or consumer?'),
    ]),
    (8, "Unit 8: Comparative Advantage", [
        (1, 'What is absolute advantage?'),
        (2, 'Instead of what?'),
        (3, 'What does comparative advantage look like?'),
        (4, 'How does comparative advantage give you an advantage?'),
    ]),
    (9, "Unit 9: Specialization & Trade", [
        (1, 'What is specialization?'),
        (2, 'How are specialization and trade related?'),
        (3, 'Who benefits from trade?'),
        (4, 'What can trade do for you?'),
    ]),
    (10, "Unit 10: Transaction Costs", [
        (1, "Is free trade 'free?'"),
        (2, 'What are the different types of transaction costs?'),
        (3, 'How do you mitigate transaction costs?'),
        (4, 'What transactions costs do you face?'),
    ]),
    (11, "Unit 11: Barter", [
        (1, 'What is barter?'),
        (2, 'Is barter efficient?'),
        (3, 'What comes after barter?'),
        (4, 'How do you trade?'),
    ]),
    (12, "Unit 12: Money", [
        (1, 'How does money help us make exchanges?'),
        (2, 'How do we know what to trade?'),
        (3, 'How does money retain value?'),
        (4, 'What does money do for you?'),
    ]),
    (13, "Unit 13: Properties of Money", [
        (1, 'How do we transport money?'),
        (2, 'How much money should there be?'),
        (3, 'How is money divided?'),
        (4, 'What do you want money to be?'),
    ]),
    (14, "Unit 14: Demand", [
        (1, 'What is demand?'),
        (2, 'How do individuals decide what to buy?'),
        (3, 'What is market demand?'),
        (4, 'Where do we see demand curves in real life?'),
    ]),
    (15, "Unit 15: Shifts in Demand", [
        (1, 'What is the relationship between goods?'),
        (2, 'What changes demand?'),
        (3, 'How much does demand change?'),
        (4, 'When is demand wrong?'),
    ]),
    (16, "Unit 16: Supply", [
        (1, 'What is supply?'),
        (2, 'How much does the market supply?'),
        (3, 'How does supply change?'),
        (4, 'When is supply wrong?'),
    ]),
    (17, "Unit 17: Market Equilibrium", [
        (1, 'Where do supply and demand meet?'),
        (2, 'Who benefits from clearing the market?'),
        (3, 'Can the government control supply and demand?'),
        (4, 'How do supply and demand affect you?'),
    ]),
    (18, "Unit 18: Time & Value", [
        (1, 'When do we receive value?'),
        (2, 'When do you want your money?'),
        (3, 'What is interest?'),
        (4, 'What does interest do for us?'),
    ]),
    (19, "Unit 19: Banks", [
        (1, 'What are banks?'),
        (2, 'Where do you save your money?'),
        (3, 'What do banks do with our deposits?'),
        (4, 'How do banks lend your money?'),
    ]),
    (20, "Unit 20: Keynesianism & Central Banks", [
        (1, 'Who put the "Keynes" in Keynesianism?'),
        (2, 'What is the price of money?'),
        (3, 'What do central banks do?'),
        (4, 'Is Keynesianism relevant today?'),
    ]),
    (21, "Unit 21: Inflation", [
        (1, 'What is the value of money?'),
        (2, 'Why is inflation bad?'),
        (3, 'Where do we see inflation in real life?'),
        (4, 'How can we prevent inflation?'),
    ]),
    (22, "Unit 22: Capital & the Austrian View", [
        (1, 'What is capital?'),
        (2, 'How do Austrians see the economy?'),
        (3, 'Why is Keynesianism wrong?'),
        (4, 'Are Austrians correct in real life?'),
    ]),
    (23, "Unit 23: Firms & Externalities", [
        (1, 'What is (and is not) a firm?'),
        (2, 'How do firms grow?'),
        (3, 'What costs do firms have?'),
        (4, 'What are externalities?'),
    ]),
    (24, "Unit 24: Competition & Monopoly", [
        (1, 'How many firms are in a market?'),
        (2, 'Are monopolies bad?'),
        (3, 'How do monopolies work in real life?'),
        (4, 'How is the government a monopoly?'),
    ]),
    (25, "Unit 25: Taxes", [
        (1, 'Are taxes voluntary?'),
        (2, "Do taxes change people's behavior?"),
        (3, 'How is the government funded?'),
        (4, 'Where do we see taxes in real life?'),
    ]),
    (26, "Unit 26: World Trade & Currencies", [
        (1, 'What money do people use around the world?'),
        (2, 'How do people compare monies?'),
        (3, 'How does the government limit trade?'),
        (4, 'How has world trade changed?'),
    ]),
    (27, "Unit 27: Investing & Risk", [
        (1, 'What is investing?'),
        (2, "What's the downside of investing?"),
        (3, 'How do we beat risk?'),
        (4, 'How do people invest in real life?'),
    ]),
    (28, "Unit 28: Public Choice Theory", [
        (1, 'What is public choice theory?'),
        (2, 'How do people make decisions when voting?'),
        (3, 'How does a bureaucracy work?'),
        (4, 'Is public choice theory useful?'),
    ]),
    (29, "Unit 29: Socialism & the Calculation Problem", [
        (1, 'What is socialism?'),
        (2, 'How would a central planner know what people want?'),
        (3, 'Do socialists use prices?'),
        (4, 'Has socialism worked in real life?'),
    ]),
    (30, "Unit 30: Entrepreneurship", [
        (1, 'How do economists think?'),
        (2, 'Does technology change economics?'),
        (3, 'What are the benefits of entrepreneurship?'),
        (4, 'How can you think like an entrepreneur?'),
    ]),
]


def build_tasks():
    """Flatten to one task per lesson, in teaching order."""
    out = []
    for num, unit_title, lessons in UNITS:
        short = unit_title.split(":")[0].strip()
        for ln, title in lessons:
            out.append({
                "title": f"FMR {short} L{ln}: {title}",
                "unit": unit_title,
                "category": CATEGORY,
                "task_type": "project" if ln == 4 else "lesson",
                "xp": LESSON_XP,
                "minutes": LESSON_MINUTES,
            })
    return out


TASKS = build_tasks()


if __name__ == "__main__":
    print(f"{len(UNITS)} units, {len(TASKS)} lessons")
    for t in TASKS[:5] + TASKS[-3:]:
        print(f"  [{t['task_type']:<7}] {t['title']}")
