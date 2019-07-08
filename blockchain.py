import hashlib
import json
from datetime import datetime
import random
import socket
import select
import sys
import copy
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor


blockname=''
transval=0
from_addr=''
to_addr=''

class Block():

    def __init__(self,block_type,nonce,timestamp,transaction, to_address, from_address, prevhash=''):
	self.block_type=block_type
        self.nonce=nonce
        self.timestamp=timestamp
        self.transaction=transaction
        self.to_address=to_address
        self.from_address=from_address
        self.prevhash=prevhash
        self.hash=self.calcHash()

    def calcHash(self):
        block_string=json.dumps({"nonce":self.nonce, "timestamp":self.timestamp, "transaction":self.transaction, "prevhash":self.prevhash}, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def mineBlock(self,difficulty):
        while(self.hash[:difficulty] != str('').zfill(difficulty)):  #check number of zeros in hash is equal to set difficulty value
            self.nonce += 1
            self.hash=self.calcHash()
        #print("Mined Block:",self.hash)

    def __str__(self):
	string="Block Type:\t" + str(self.block_type) + "\n"
        string+="Nonce:\t" + str(self.nonce) + "\n"
        string+="Timestamp:\t" + self.timestamp + "\n"
        string+="Transaction:\t" + str(self.transaction) + "\n"
        string+="To Address:\t" + str(self.to_address) + "\n"
        string+="From Address:\t" + str(self.from_address) + "\n"
        string+="Previous Hash:\t" + self.prevhash + "\n"
        string+="Current Hash:\t" + self.hash
        return string



class BlockChain():

    def __init__(self):
        self.chain=[self.generateGenesisBlock(),]
        self.difficulty=3

    def generateGenesisBlock(self):
        return Block("Genesis Block",0,str(datetime.now()),'Genesis Block','','')

    def getLastBlock(self):
        return self.chain[-1]

    def addNewBlock(self, newBlock):
        newBlock.prevhash=self.getLastBlock().hash
        #newBlock.hash=newBlock.calcHash()
        newBlock.mineBlock(self.difficulty)
        self.chain.append(newBlock)

    def isValid(self):
        string=''
        for index in range(1,len(self.chain)):
            prevb=self.chain[index-1]
            currb=self.chain[index]
            if(currb.hash != currb.calcHash()):
                string+="BlockChain Tampered :: Error in Computing Hash!!\n"
                return string, False
            if(prevb.hash != currb.prevhash):
                string+="BlockChain Tampered :: Error in Computing Hash!!\n"
                return string, False
        string+="BlockChain is Valid!!!\n"
        return string, True

    def get_total_transactions(self):
        address_set=[]
        for index in range(1,len(self.chain)):
            if self.chain[index].to_address not in address_set:
                address_set.append(self.chain[index].to_address)
            if self.chain[index].from_address not in address_set:
                address_set.append(self.chain[index].from_address)

        incoming=0
        outgoing=0
        string=''
        for enum,addr in enumerate(address_set):
            for index in range(1,len(self.chain)):
                if addr == self.chain[index].to_address:
                    incoming+= self.chain[index].transaction
                if addr == self.chain[index].from_address:
                    outgoing-= self.chain[index].transaction
            string+="################ Net Transactions for {} #################\n".format(address_set[enum])
            string+="Incoming Transactions: {}\n".format(incoming)
            string+="Outgoing Transactions: {}\n".format(outgoing)
            incoming=0
            outgoing=0
        return string


    def viewBlockchain(self):
    	string=''
        for index, block in enumerate(self.chain):
            string+="#########################" + " Block " + str(index) + " #########################\n"
            string+=block.__str__()+"\n"
    	return string

    def lenBlockchain(self):
	length=0
	for index, block in enumerate(self.chain):
	    length+=1
	return length


class BlockChainP2P(LineReceiver):

    def __init__(self, users,instances):
	#self.blockname=''
	#self.to_addr=''
	#self.transval=0
	#self.from_addr=''
        self.instances= instances
        #self.instances[]={self.useself.blockchain=BlockChain()}
        self.blockchain=BlockChain()
        self.users = users
        self.name = None
        self.state = "GETNAME"
	self.allowed={"Supplier":"supplier","CompanyA":"compa", "CompanyB":"compb", "CBDT":"cbdt", "Auditors":"auditors"}



    def connectionMade(self):
        self.sendLine("[*]Enter \"help\" to list all the Available Commands")
        self.sendLine("[?]Enter UserName and Password")

    def connectionLost(self,reason):
        if self.name in self.users:
            del self.users[self.name]

    def lineReceived(self, line):
        if self.state == "GETNAME":
            self.handle_GETNAME(line)
        else:
            self.handle_CHAT(line)

    def handle_GETNAME(self, name):
	arguments = name.split(" ")
	if(len(arguments)!=2):
	    sendLine("Format for Entering is [Username] [Password]")
	    self.transport.loseConnection()

	if arguments[0] in self.allowed and self.allowed[arguments[0]] == arguments[1] and arguments[0] not in self.users:
	    self.sendLine("Welcome, %s!" % (arguments[0]))
	    name=arguments[0]
	    self.name=name
	    self.users[name]=self
	    self.instances[name]=copy.deepcopy(self.blockchain)
            self.state = "CHAT"

	else:
	    self.sendLine("Invalid Username and Password!!!")
	    if arguments[0] in self.users:
		del self.users[self.name]
	    self.transport.loseConnection()




    def handle_CHAT(self, message):
        arguments = message.split(" ")
    	if arguments[0] == "exit":
    		if self.name in self.users:
    			del self.users[self.name]
    		self.transport.loseConnection()

        elif arguments[0] == "help":
            message = "\n[*]Available Commands\n\n"
            message += "exit: Disconnects from the server\n\n"
            message += "verify: Checks the validity of the blockchain\n\n"
            message += "view: Shows the entire blockchain\n\n"
            message += "transactions: Lists all the Incoming and Outgoing Transactions for each Participant\n\n"
            message += "list: Lists all the current online users\n\n"
            message += "add <from address> <to address> <transaction quantity>: Mines a new block which is added to the blockchain\n\n"
            message += "update: Checks for all the local bloackchain Instances of the Users and Updates all the chains with the latest chain\n\n"
	    message += "adjust: Checks between the Value difference between Sales Block and Expenditure Block and sends the corresponding tax value to CBDT\n\n"

    	elif arguments[0] == "verify":
		message = "\n[*]Verifying Blockchain Hash\n"
		string,switch = self.instances[self.name].isValid()
    		#string,switch=self.blockchain.isValid()
    		message+=string

    	elif arguments[0] == "view":
    		message= "\n[*]Retrieving Blockchain\n"
    		#message+=self.blockchain.viewBlockchain()
		message += self.instances[self.name].viewBlockchain()

    	elif arguments[0] == "transactions":
    		message = "\n[*]Listing all Transactions on Blockchain\n"
    		message += self.instances[self.name].get_total_transactions()

    	elif arguments[0] == "list":
    		message = "\n[*]Listing Online Users\n"
    		for user in self.users:
			user_arg=user.split(" ")
    			message += "\n" + user_arg[0]

    	elif arguments[0] == "add":
            if len(arguments)<4:
                message="Command Format :: add <block type> <to address> <transaction quantity>:"
            elif len(arguments)==4 and (arguments[1]=="Sales" or arguments[1]=="Expenditure"):
		global blockname
		blockname = arguments[1]
		global from_addr
		from_addr = self.name
		global to_addr
		to_addr = arguments[2]
		global transval
		transval = arguments[3]
		msg=''
                msg = "Please Verify the Transaction!!!\n"
                msg += "Block Type: " + str(blockname) + "\n"
                msg += "From Address: " +str(from_addr) + "\n"
                msg += "To Address: " + str(to_addr) + "\n"
                msg += "Transaction Value: " + str(transval)+"\n"
		message="[!!] Waiting for Apprroval from the Other Party!!"
                for name, protocol in self.users.iteritems():
                        if name == arguments[2]:
                                protocol.sendLine(msg)

	    else:
		message="\n[!] Error in command!! Only \"Sales\" and \"Expenditure\" Blocks are Valid!!\n"

		#message = "\n[*]Adding New Block for Transaction\n"
		#for name in self.instances.keys():
			#self.blockchain.addNewBlock(Block(random.randint(1,1001),str(datetime.now()),int(arguments[3]),arguments[1],arguments[2]))
		#	self.instances[name].addNewBlock(Block(random.randint(1,1001),str(datetime.now()),int(arguments[3]),arguments[1],arguments[2]))
    		#self.blockchain.addNewBlock(Block(random.randint(1,1001),str(datetime.now()),50,'Addr1','Addr2'))

	elif arguments[0] == "checked":
	    message = "\n[*]Adding New Block for Transaction\n"
#	    global blockname
#	    global transval
#	    global from_addr
#	    global to_addr
#	    print(blockname)
#	    print(transval)
#	    print(from_addr)
#	    print(to_addr)
	    for nm in self.instances.keys():
	        self.instances[nm].addNewBlock(Block(blockname,random.randint(1,1001),str(datetime.now()),float(transval),str(from_addr),str(to_addr)))

	elif arguments[0] == "update":
	    maxval=0
	    final=''
	    for name in self.instances.keys():
	        if self.instances[name].lenBlockchain()>maxval:
		    final=name
		    maxval=self.instances[name].lenBlockchain()
	    for name in self.instances.keys():
	        if name!=final:
		    self.instances[name]=copy.deepcopy(self.instances[final])
	    message="\n[*]The entire Blockchain has been Updated!!\n"


	elif arguments[0] == "adjust":
	    expenditure=0
	    profit=0
            sales=0
	    flag=0
	    if self.instances[self.name].chain[-2].block_type=="Expenditure":
		expenditure=self.instances[self.name].chain[-2].transaction
		sales=self.instances[self.name].chain[-1].transaction
		flag=1
	    elif self.instances[self.name].chain[-1].block_type=="Expenditure":
		expenditure=self.instances[self.name].chain[-1].transaction
		sales=self.instances[self.name].chain[-2].transaction
		flag=1
	    else:
		message="\n[!]The ordering of the Blocks should have Expenditure->Sales or Sales->Expenditure\n"
	    if flag==1:
	        profit=sales-expenditure
	        threshold=float(14.5*expenditure)/float(100)
#	        print(profit)
#	        print(threshold)
#	        print(sales)
#	        print(expenditure)
	        if profit > threshold:
		    message="\n[*]No Adjustment Required!!\n"
	        else:
		    transval=(threshold-profit)*0.25
		    for nm in self.instances.keys():
                        self.instances[nm].addNewBlock(Block("Adjustment",random.randint(1,1001),str(datetime.now()),float(transval),"Company","CBDT"))


    	else:
    		message = "\n[!]Command Does Not Exist\n"


        message = "%s\n" % (message)
        for name, protocol in self.users.iteritems():
            if protocol == self:
                protocol.sendLine(message)


class BlockChainFactory(Factory):

    def __init__(self):
        self.users = {} # maps user names to Chat instances
        self.instances = {}
    def buildProtocol(self, addr):
        return BlockChainP2P(self.users,self.instances)


reactor.listenTCP(8123, BlockChainFactory())
reactor.run()

