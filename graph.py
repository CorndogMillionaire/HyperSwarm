from HyperSwarm.api import Generate
from colorama import Fore, Back, Style
import textwrap
import chromadb
import time
import datetime
from chromadb.utils import embedding_functions
from chromadb.config import Settings
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name='all-mpnet-base-v2')
chroma_client = chromadb.Client(Settings(anonymized_telemetry=False))

def check_lowest_level_type(container, preset_type):
    for element in container:
        if isinstance(element, (list, tuple, set, frozenset)):
            if not check_lowest_level_type(element, preset_type):
                return False
        elif not isinstance(element, preset_type):
            return False
    return True
def fill_prompt(pt:str,inputs:dict):
    curtime = datetime.datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
    prompt = pt
    for input in inputs:
        prompt=prompt.replace("{"+input+"}",inputs[input])
    prompt=prompt.replace("{Time}",curtime)
    return prompt

class Node:
    def __init__(self,id,instruction,context="",default_output = "",memory_enable=True):
        self.id = id
        self.context = context
        self.instruction = instruction
        self.output = default_output
        self.memory_enable=memory_enable
        if self.memory_enable:
            #We create a collection with a unique name for the node to store the memories in using an embedding function to encode whatever is edded and convert it into a vector embedding
            self.memories = chroma_client.create_collection(f"{self.id}_collection", embedding_function=sentence_transformer_ef)
            self.memory_threshold = 1
    def update(self,inputs,hyperpt):
        # Replacing the {ID} occurences inside self.context and self.instruction with the corresponding inputs
        context_fill = fill_prompt(self.context,inputs)
        fill = fill_prompt(self.instruction, inputs)
        #Initializing the metaprompt, this is everything that will be fed to the LLM
        metaprompt = ""

        if self.memory_enable:
            #Initializing the retrieved relevant memories and the topics to search for in memories
            relevant_memories=""
            Topics=""
            #Iterate over the inputs and make a string that contains all inputs
            for input in inputs:
                # print(Fore.LIGHTMAGENTA_EX + "[DEBUG]:" + Fore.WHITE + input + ":" + inputs[input])
                Topics+=f"{input}:{inputs[input]}"
                # Topics += "\n"+Generate(f"{input}:{inputs[input]}\n Extract relevant topics from the above and write them separated by comma. Example: Topic2,Topic2, etc\nExtracted Topics:")
            #Using the LLM to generate a list of topics that are in the inputs
            Topics=Generate(f"{Topics}\n Extract relevant topics from the above and write them separated by comma. Example: Topic2,Topic2, etc Write only the topics\nExtracted Topics:")
            print(Fore.RED+"[MEMQUERY]:"+Fore.WHITE+Topics)

            #Quering the memory collection for the topics we created using the LLM
            memories=self.memories.query(query_texts=Topics)

            #If any memories were found
            if len(memories['documents'][0])>0:
                #We go through each memory with their distances respective to the topics
                for memory, distance in zip(memories['documents'][0],memories['distances'][0]):
                    #And we check if the distance is below a threshold to only retrieve closely related entries
                    if distance <= self.memory_threshold:
                        #We add the memories to the relevant memories
                        relevant_memories+=memory+"\n"
                #Check if there is anything there
                if relevant_memories!="":
                    print(Fore.RED+"Relevant memories: "+relevant_memories)
                    #We use an LLM to update the entirety of all relevant memories with a summary
                    relevant_memories=Generate(relevant_memories+"\nSummarize the above compactly, concisely and abstract.\nSummary:")
            #Just to debug we look at the summary of the memories
            print(Fore.RED + "[MEMRESULT]:" + Fore.WHITE + relevant_memories)
            #Structuring the metaprompt for the memory enabled nodes, we check if there is context
            if self.context !="":
                metaprompt=f"###Context\n#Memories:\n{relevant_memories}\n{context_fill}\n\n###Instruction:{hyperpt}\n{fill}\n###Assistant:"
            else:
                metaprompt=f"###Context\n#Memories:\n{relevant_memories}\n\n###Instruction:{hyperpt}\n{fill}\n###Assistant:"
        #If there is no memory we just check for context
        else:
            if self.context!="":
                metaprompt=f"###Context\n{context_fill}\n\n###Instruction:{hyperpt}\n{fill}\n###Assistant:"
            else:
                metaprompt=f"###Instruction:{hyperpt}\n{fill}\n###Assistant:"

        #Quick debug to print out the entirety of whats fed to the LLM
        print(Fore.RED+"[DEBUG:]"+Fore.LIGHTMAGENTA_EX + metaprompt)

        # Generate the Output and update the output attribute
        self.output = Generate(metaprompt)
        # Now if memory is enabled we add all the inputs the node received during this update to the nodes memory
        curtime = datetime.datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        if self.memory_enable:
            #We add what node it came from and what the output of it was in relation to its ID which is a combination of our own ID with a unique time identified to avoid duplicate ids
            #For the future i need to add the timestamp to the metadata here
            self.memories.add(documents=[f"{self.id}:"+self.output], ids=[f"{self.id}+{time.time()}"])
            for input in inputs:
                self.memories.add(documents=[f"{input}:{inputs[input]}"],ids=[f"{input}{time.time()}"])
        #print(textwrap.fill(Fore.RED+f"[{self.id}]:"+Fore.YELLOW+self.output, width=160))
        #Just printing what the node output was after updating
        print(Fore.RED + f"[{self.id}]:" + Fore.YELLOW + self.output)

class Hyperedge:
    def __init__(self,id,inputs,outputs,hyperpt="", order="forward"):
        self.id=id
        self.hyperpt=hyperpt
        self.input_nodes=inputs
        self.output_nodes=outputs
        self.order = order
    def add(self,inputs,outputs:list):
        try:
            if check_lowest_level_type([inputs,outputs],Node):
                self.input_nodes.extend(inputs)
                self.input_nodes = list(set(self.input_nodes))
                self.output_nodes.extend(self.output_nodes)
                self.output_nodes = list(set(outputs))
            else:
                raise TypeError(inputs)
        except TypeError as e:
            print(Fore.RED+"TypeError: Couldn't add object")

    def remove(self,inputs,outputs:list):
        try:
            if check_lowest_level_type([inputs,outputs],Node):
                self.input_nodes = [x for x in self.input_nodes if x not in inputs]
                self.input_nodes = list(set(self.input_nodes))
                self.output_nodes = [x for x in self.output_nodes if x not in outputs]
                self.output_nodes = list(set(self.output_nodes))
            else:
                raise TypeError(inputs)
        except TypeError as e:
            print(Fore.RED+"TypeError: Couldn't add object")
    def initialize(self):
        for node in self.input_nodes:
            node.update()

    def update(self):
        # Normal forward order, output nodes update method are called with the outputs from all input nodes
        if self.order == "forward":
            #Empty output dictionary linking input node ids to their output
            outputs = {}
            # creating the dictionary by making a list of outputs from the input nodes
            for node in self.input_nodes:
                # we collect the node output accessible through its node id in the outputs dictionary
                outputs[node.id] = node.output
            # passing the input dictionary to the output nodes
            for node in self.output_nodes:
                #we call the output nodes update method, feeding it the outputs of all connected nodes aswell as the hyperedges prompt template
                node.update(outputs,self.hyperpt)
        # reverse order, inputs are called with the output from all output nodes
        if self.order == "reverse":
            outputs = {}
            # creating the dictionary by making a list of outputs from the output nodes
            for node in self.output_nodes:
                # we collect the node output accessible through its node id in the outputs dictionary
                outputs[node.id] = node.output
            # passing the input dictionary to the input nodes
            for node in self.output_nodes:
                #we call the input nodes update method, feeding it the outputs of all connected output nodes aswell as the hyperedges prompt template
                node.update(outputs,self.hyperpt)



purpose = "A python framework that downloads a github repo and makes a list of files. The goal is to make a collection of text snippeds from these files that can easily be retrieved by a semantic search"
Purpose=Node(
    "Purpose",
    "",
    "",
    default_output=purpose
)
Coder=Node(
    "Coder",
    "Code a function with the purpose: '{Purpose}'. Write verbose comments inside the code for documentation. Code:",
    "You are an expert in coding python. You write python code.\nGuidelines: Verbosely write commentary in the code to help readability of the code",
    memory_enable=False
)
Analyzer=Node(
    "Analyzer",
    "Critically Assess and Analyze only the above code, nothing else. Understand what the code does. Think step by step and write it down",
    "Code:{Coder}",
    memory_enable=False
)
Feedback=Node(
    "Feedback",
    "Based on the analysis, will the code fulfill its purpose? Write critque and a review of the code and argue in clear and concise step by step reasoning what can be improved, what needs to be added, what needs to be removed in regards to the purpose: {Purpose}.",
    "Purpose:{Purpose}\nCode:{Coder}\nAnalysis:{Analyzer}",
    memory_enable=False
)
Refiner=Node(
    "Refiner",
    "Based on the feedback, improve the code so it better fulfilles its purpose: {Purpose}. Only write the improved code. Code:",
    "Purpose:{Purpose}\nOriginal Code:{Coder}\nFeedback:{Feedback}\nGuidelines: Always write commentary to your functions to help readability of the  code",
    memory_enable=False
)
GenerateCode = Hyperedge(
    "Code",
    [Purpose],
    [Coder]
)
GenerateAnalysis = Hyperedge(
    "Analyze",
    [Purpose,Coder],
    [Analyzer]
)
GenerateFeedback = Hyperedge(
    "Feedback",
    [Purpose,Coder,Analyzer],
    [Feedback]
)
RefineCode = Hyperedge(
    "Refine",
    [Purpose,Coder,Feedback],
    [Refiner]
)
#First writing of the code
GenerateCode.update()

for i in range(1,100):
    print(Fore.GREEN+f"++++++++++++++++++CYCLE[{i}]+++++++++++++++++")
    GenerateAnalysis.update()
    GenerateFeedback.update()
    RefineCode.update()
    Coder.output = Refiner.output
    print(Fore.GREEN+"++++++++++++++++++NEW CYCLE+++++++++++++++++")