# TEAM NAME - CC_0213_1566_1573

# Mini DBaaS for Rideshare

*	Code for final DBaaS phase is in folder ``` /Last ```.

*	We assume that the basic required setup such as the LoadBalancer is already done.

### Steps to run
```
cd Last/
```
		Folder Named Last contains the final project code
		SETUP for Orchestrator VM
		To run the entire setup of Orchestrator VM
				cd DBaas/
				sudo docker-compose up -d --build

		The code for the Orchestrator	: 	/DBaas/Orchestrator
		The code for the Worker		:	/DBaas/Worker

		Orchestrator split into 3 different files
		Main Application code			:	/DBaas/Orchestrator/app_orchestrator.py
		helper code				:	/DBaas/Orchestrator/helper.py
		global constants			: 	/DBaas/Orchestrator/constants.py

		Worker split into 3 different files
		Main Application code			:	/DBaas/Worker/app_worker.py
		helper code				:	/DBaas/Worker/worker_helper.py
		global constants			:	/DBaas/Worker/constants.py

		SETUP for Rides VM
		The code for the Rides			: 	/Rides
		To run the entire setup of Rides VM
				sudo docker-compose up -d --build
		
		SETUP for Users VM
		The code for the Rides			: 	/Users
		To run the entire setup of Users VM
				sudo docker-compose up -d --build

#Assignment 3 code in CC3
#We assume that the required setup such as the LoadBalancer is already setup
		cd CC3/
		Folder Named CC3 containes Assignment3 code
		SETUP for Users VM:
			cd Users/
			sudo docker-compose up -d --build
		
		SETUP for Rides VM:
			cd Rides/
			sudo docker-compose up -d --build

#Assignment 2 code in CC2

		cd CC2/
		Folder Named CC2 contains Assignment2 code
		SETUP for all the required containers:
			sudo docker-compose up -d --build

#Assignment 1 code in CC1

		cd CC1/
		sudo python3 datasetup.py
		sudo python3 app_server.py
