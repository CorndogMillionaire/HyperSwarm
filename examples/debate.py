topic = "Is AI-art real art?"
Alice=Node(
    "Alice",
    "You are to roleplay as Alice, be polite, emotional, ethical and moral and friendly and very agreeable\nWrite a message starting with Alice:",
    "#Previous Summary:\n{Summary}\n#New Messages:\n{Bob}\n{Carl}\n{Steve}\n#Time it is now {Time}",
    "Alice:Hey, i'm Alice, i'm so happy to meet you two!")
Bob=(Node(
    "Bob",
    "You are to roleplay as Bob, behave rude and impolite and take a contrarian position to disagree on everything\nWrite a message starting with Bob:",
    "#Previous Summary:\n{Summary}\n#New Messages:\n{Carl}\n{Alice}\n{Steve}\n#Time it is now {Time}",
    "Bob:whats up idiots, i'm bob"
))
Carl=Node(
    "Carl",
    "You are to roleplay as Carl, behave rational and unempathic and present your arguments and your thoughts in steps\nWrite a message starting with Carl:",
    "#Previous Summary:\n{Summary}\n#New Messages:\n{Bob}\n{Alice}\n{Steve}\n#Time it is now {Time}",
    "Carl:Sup, i'm carl"
)
Steve=Node(
    "Steve",
    "You are to roleplay as Steve, have no regards for moral or ethics,be unempathic but intelligent and extremely direct, present your rationale and your thoughts in precise steps.\nWrite a message starting with Steve:",
    "#Previous Summary:\n{Summary}\n#New Messages:\n{Bob}\n{Alice}\n{Carl}\n#Time it is now {Time}",
    "Steve:Hey, i'm Steve."
)
Summarizer=Node(
    "Summary",
    "Concisely summarize the key arguments about the topic from the conversation by extending the already existing summary with the summary of the new messages. Write everything in past tense, clear and concise language and focus on the topic.",
    "#Previous Summary: {Summary}\n#New Messages:\n{Bob}\n{Alice}\n{Carl}\n{Steve}",
    "",
    False
)
Broadcast=Hyperedge(
    "Multidirectional Broadcast",
    [Steve, Alice, Bob, Carl, Summarizer],
    [Alice, Bob, Carl, Steve],
    f"You are in a broadcast. Everything said will be broadcasted to everyone in it. Todays discussion is about {topic}. Stay on topic."
)
Feedback=Hyperedge(
    "Summarizer",
    [Steve, Alice, Bob, Carl, Summarizer],
    [Summarizer],
    f"You are listening to a broadcast with the topic {topic}"
)
for i in range(1,10):
    print(Fore.GREEN+f"++++++++++++++++++CYCLE[{i}]+++++++++++++++++")
    Broadcast.update()
    Feedback.update()
    print(Fore.GREEN+"++++++++++++++++++NEW CYCLE+++++++++++++++++")
