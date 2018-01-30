import os,os.path,time
import igraph
from igraph import *
import sqlite3

g = Graph()
baseDir = '/home/agnieszka'               #base/considered directory
fileName ='pro'                                   #part of a searched file name

#class responsible for graph creation
class dirTree():
    
    def __init__(self, graph):
        self.g = graph

    #find content of a directory
    #specify graph's verteces and edges
    def findNodes(self, rootDir):
        self.g.add_vertex(rootDir)                              #add a vertex to the graph
        self.g.vs.find(rootDir)['att'] = 'dir'                  #attribute specifies if vertex is a file, dir or root dir
        self.g.vs[0]['att'] = 'root'                                  #used also to give verteces different colors
        for nodeName in os.listdir(rootDir):               #list of all items in a directory
            nodePath = rootDir+'/'+nodeName
            if (not nodeName.startswith('.')):                #continue if found item isn't hidden 
                if (os.path.isfile(nodePath) == 1):           #consider item if it is a file
                    self.g.add_vertex(nodePath)                   
                    self.g.add_edge(rootDir, nodePath)        #connetion to the folder in which file was found
                    self.g.vs.find(nodePath)['att']='file'
                    self.g.vs.find(nodePath)['lastChange'] =time.ctime(os.path.getmtime(nodePath))       #node attribute - last change time of a file
                    self.g.vs.find(nodePath)['fileSize'] = os.stat(nodePath).st_size                                        #node attribute - file size
                else:                                                               #in case a folder was found
                    self.findNodes(nodePath)                          # call a function itself, to list its content
                    self.g.add_edge(rootDir, nodePath)        

    #graph's settings and plot request 
    def plotGraph(self):                                                                        
        color_dict = {"file": "blue", "dir": "yellow", "root": "red"}
        self.g.vs["color"] = [color_dict[att] for att in self.g.vs["att"]]
        layout = self.g.layout("rt")
        plot(self.g, layout = layout)

#class responsible for inserting graph data to database
#and looking for a file in a database
class graphDatabase():

    def __init__(self, graph, database, tableName):
        self.g = graph
        tableName = tableName.replace("/","_")              #name of a table is equal to the considered base directory, name change is needed for sql query
        self.tb = tableName
        self.db = database

     #creation of a table    
    def createTable(self):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        sql = 'CREATE TABLE IF NOT EXISTS '+self.tb+' (name TEXT PRIMARY KEY, size INT , lastChange TEXT )'
        c.execute(sql)
        conn.commit()
        conn.close()

    #inserting records to the table
    def updateTable(self):
        k=[]                                                            #list of lists including attributes of graph verteces
        k.append(self.g.vs['name'])                                          
        k.append(self.g.vs['fileSize'])
        k.append(self.g.vs['lastChange'])
        
        result=zip(*k)                                          #manipulation of lists-list
        result=list(result)                                     #in order to obtain list, which is acceptable for sql INSERT query
        
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        sql = 'INSERT OR REPLACE INTO ' + self.tb + '(name, size, lastChange) VALUES (?, ?, ?)'
        c.executemany(sql,result)
        conn.commit()
        conn.close()

    #looking for a file where only a part of a name [fname] is known
    def findFile(self, fname):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()                                                           #in database only files have size different than null
        c.execute("SELECT * FROM " + self.tb + " WHERE name LIKE ('%/"+fname+"%') AND size NOT NULL ")
        result = c.fetchall()
        for x in result:                                    #also files which have given string [fname] in their path will be shown
            print(x)
        conn.commit()
        conn.close()

graph = dirTree(g)
graph.findNodes(baseDir)        
graph.plotGraph()

graphDb = graphDatabase(g, 'test.db', baseDir)
graphDb.createTable()
graphDb.updateTable()
graphDb.findFile(fileName)
