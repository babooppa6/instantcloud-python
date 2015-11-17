# Instant Cloud API - Python client

This repository contains sample Python code for making API requests to
the Gurobi Instant Cloud.  This sample code is provided for
illustration purposes; it is not covered by the support terms of the
Gurobi End User License Agreement.

## Obtaining this repository

If you have git installed, you can obtain this repository, by cloning it, with the following command:

```
git clone https://github.com/Gurobi/instantcloud-python.git
```

If you don't have git installed, click the Download Zip button in the right sidebar.

## Requirements

The `instantcloud.py` program requires the following Python modules: `hmac`, `hashlib`, `urlib`, and
`urllib2`. The `instantcloud.py` program uses Python 2.7. It does not yet support Python 3.

## Using instantcloud.py from the command-line

The `instantcloud.py` program can be used as a command-line client for the API. It provides
access to the four API endpoints: licenses, machines, launch, kill.

### List your licenses

Run the following command to list your licenses:

```
./instantcloud.py licenses --id INSERT_YOUR_ID_HERE --key INSERT_YOUR_KEY_HERE
```

You should see output like the following:
```
License Credit  Rate Plan       Expiration
95912   659.54  standard        2016-06-30
95913   44.10   nocharge        2016-06-30
```

### List your running machines

Run the following command to list your running machines

```
./instantcloud.py machines --id INSERT_YOUR_ID_HERE --key INSERT_YOUR_KEY_HERE
```

You should see output like the following:

```
Machine name:  ec2-54-85-186-203.compute-1.amazonaws.com
        license type:  light compute server
        state:  idle
        machine type:  c4.large
        region:  us-east-1
        idle shutdown:  60
        user password:  a446887d
        create time:  2015-10-14T20:27:01.224Z
        license id:  95856
        machine id:  xjZTbW9tdqbT32Cep
```


### Launch a machine

Run the following command to launch a machine

```
./instantcloud.py launch --id INSERT_YOUR_ID_HERE --key INSERT_YOUR_KEY_HERE -n 1 -m c4.large
```

You should see output similar to the following
```
Machines Launched
Machine name:  -
        license type:  light compute server
        state:  launching
        machine type:  c4.large
        region:  us-east-1
        idle shutdown:  60
        user password:  a446887d
        create time:  2015-10-14T20:27:01.224Z
        license id:  95856
        machine id:  xjZTbW9tdqbT32Cep
```


### Kill a machine

Run the following command to kill a machine

```
./instantcloud.py kill --id INSERT_YOUR_ID_HERE --key INSERT_YOUR_KEY_HERE xjZTbW9tdqbT32Cep
```

You should see output similar to the following

```
Machines Killed
Machine name:  ec2-54-85-186-203.compute-1.amazonaws.com
        license type:  light compute server
        state:  killing
        machine type:  c4.large
        region:  us-east-1
        idle shutdown:  60
        user password:  a446887d
        create time:  2015-10-14T20:27:01.224Z
        license id:  95856
        machine id:  xjZTbW9tdqbT32Cep

```

## Using instantcloud.py as a library

You can use `instantcloud.py` as a library within your own Python programs to make
API calls.

Here is a sample Python application, for Gurobi 6.0.5, that uses the `InstantCloudClient`
class to solve a MIP on a Instant Cloud machine.

```
#!/usr/bin/python

import time
from instantcloud import InstantCloudClient
from gurobipy import *

def is_machine_ready(machines):
    ready = False
    for machine in machines:
        if machine['state'] == 'idle' or \
           machine['state'] == 'running':
            ready = True
            break
    return ready


ic = InstantCloudClient(YOUR_ACCESS_ID, YOUR_SECRET_KEY)
machines = ic.getmachines()
if len(machines) < 1:
    machines = ic.launchmachines(numMachines=1, machineType="c4.large")

while not is_machine_ready(machines):
    print 'Machine not ready. Sleeping for 30 seconds'
    time.sleep(30)
    machines = ic.getmachines()

machinename = None
userpassword = None
for machine in machines:
    if machine['state'] == 'idle' or \
       machine['state'] == 'running':
        machinename = machine['DNSName']
        userpassword = machine['userPassword']
        break

env = Env("gurobi.log", computeServers=machinename, port=GRB.DEFAULT_CS_PORT, password=userpassword)
m = Model("mip1", env)

# Create variables
x = m.addVar(vtype=GRB.BINARY, name="x")
y = m.addVar(vtype=GRB.BINARY, name="y")
z = m.addVar(vtype=GRB.BINARY, name="z")

# Integrate new variables
m.update()

# Set objective
m.setObjective(x + y + 2 * z, GRB.MAXIMIZE)

# Add constraint: x + 2 y + 3 z <= 4
m.addConstr(x + 2 * y + 3 * z <= 4, "c0")

# Add constraint: x + y >= 1
m.addConstr(x + y >= 1, "c1")

m.optimize()

print('Obj: %g' % m.objVal)

```
