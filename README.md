# TEAM NAME - CC_0213_1566_1573

# Mini DBaaS for Rideshare - Final Project

*	Code for final DBaaS phase is in folder ``` /Last ```.

*	We assume that the basic requirements such as setup of the LoadBalancer is already met.

### Steps to run
```
cd Last/
```

### Setup for the Orchestrator VM
*	To run the entire setup of Orchestrator VM execute the following two commands-
```		
cd DBaas/
```
```
sudo docker-compose up -d --build
```

### Directory

Directory of where code resides - 
1.	The code for the Orchestrator is in 	
		
	```/DBaas/Orchestrator```
2.	The code for the Worker is in	

	```/DBaas/Worker```

**The Orchestrator Codebase is split into 3 different files**
1.	Main application code is in	

	```/DBaas/Orchestrator/app_orchestrator.py```
2.	Helper code is in
	
	```DBaas/Orchestrator/helper.py```
3.	Constants mapping is in 	
	
	```/DBaas/Orchestrator/constants.py```

**The Worker Codebase is split into 3 different files**
1.	Main application code is in

	```/DBaas/Worker/app_worker.py```
2.	Helper code is in

	```/DBaas/Worker/worker_helper.py```
3.	Constants mapping is in 

	```/DBaas/Worker/constants.py```

### Setup for Rides VM
The code for the Rides functionality is in ```/Rides```
#### Steps to run the entire setup of Rides VM

```sudo docker-compose up -d --build```

		
### Setup for Users VM
The code for the Users functionality is in ```/Users```

#### Steps to run the entire setup of Users VM

```sudo docker-compose up -d --build```

# Assignment 3 
*	Assigment 3 code is in ```\CC3```

*	We assume that the basic requirements such as setup of the LoadBalancer is already met.

**Steps to run**
```cd CC3/```

Setup for Users VM:

			cd Users/
			sudo docker-compose up -d --build
		
Setup for Rides VM:

			cd Rides/
			sudo docker-compose up -d --build

# Assignment 2
*	Assigment 2 code is in ```\CC2```

		cd CC2/

*	Setup for all the required containers:
		
		sudo docker-compose up -d --build

# Assignment 1

		cd CC1/
		sudo python3 datasetup.py
		sudo python3 app_server.py
