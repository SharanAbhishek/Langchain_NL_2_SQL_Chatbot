Langchain Project Workflow:



1\) Setup data in local DB - MySQL



2\) Create DB connection instance / object using SQLAlchemy in 'database.py' file



\----

'agent.py'



3\) In 'agent.py', define custom python functions for - listing tables, fetching schema, executing 'SELECT' only statements



Apply @tool decorator on the functions using langchain.tools to later provide it to Langgraph agent



4\) Create a langgraph agent using 'create\_agent' which contains the 'llm\_model' (init\_chat\_model), 'tools', 'system prompt' and 'Checkpointer'. 



Langgraph agent will also deal with Memory / State Management through 'Checkpointing' (checkpointer for MySQL - 'langgraph.checkpoint.mysql.pymysql import PyMySQLSaver' )



\---------

App.py / Streamlit - Langgraph CHeckpointer (chat memory) + Main UI + Sidebar



5\) Create 'MySQL' connection string. Used for creating  

&#x09;	i) connectoin object = chat\_db\_engine = create\_engine(Chat\_Memory\_URI)     and 	

&#x09;	

&#x09;	ii) Checkpointer = with PyMySQLSaver.from\_conn\_string(

&#x20;   					Chat\_Memory\_URI

&#x09;			 ) as checkpointer:



&#x20;   					checkpointer.setup()



&#x20;   					agent = create\_my\_agent(checkpointer)



Feed the checkpointer to the 'agent' as shown in (ii).



**How are chats stored / persisted?**



\-> Langgrpah connects the 'checkpointer' to MySQL, and a block of code deals with storing/traking the streamlit chat / thread id, langgraph then automatically stores conversations / thread id in MySQL



&#x20;









