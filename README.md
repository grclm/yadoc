# Welcome to #YetAnotherDevOpsCourse, or YADOC

Hello there. If you stumbled upon this course - chances are you are interested in learning what DevOps is exactly. Well, the bad news is that - I am not going to tell you what DevOps is - that is for you to figure out for yourself. The good news though - we will learn some cool stuff about Kubernetes and how to deploy applications on it.

# Prerequisites

 1. First of all, if I were you - I would research what all of these words mean - in the case that you don't know them, of course: **kubernetes, kubectl, k3d, docker, web app, python** (the programming language), **containers, list_will_continue**
 2. Install something like VS Code on your computer. You can work through all of this course using nothing but **notepad** and **some generic command line terminal**, but a code editor to highlight syntax of your .py, .yaml files - will make a huge difference.
 3. Go ahead and install kubectl for your Operating System [from here](https://kubernetes.io/docs/tasks/tools/) 
 4. Install k3d [from here](https://k3d.io/v5.4.7/#installation)

# Let's go!

# Contents

- [Lesson 1](#lesson-1)
- [Lesson 2](#lesson-2)
- [Lesson 3](#lesson-3)


# Lesson 1


Once  you went through all of the prerequisites, you can start working on our setup
 
## Create a k3d cluster

Open up a terminal window and create a new k3d cluster:
   
``` bash
k3d cluster create yadoc-exposed -p "8081:80@loadbalancer" --agents 3
```

## Create a Docker image: 
   
We'll deploy a simple web application to Kubernetes, so we need to create a Docker image for our application. You can use any programming language or framework you like for your application, but for simplicity, we'll use a simple Python Flask application.
``` python
from flask import Flask
import base64

app = Flask(__name__)

@app.route('/')

def hello_world():
    decoded_text = base64.b64decode('SSBhbSB3YXRjaGluZyB5b3UsIE1hcml1cyBO').decode('utf-8')
    return decoded_text

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
    
```
This is a very basic Flask application that listens on port 5000 and returns a string when you visit the root URL.

Next, create a new file named Dockerfile with the following contents:

``` dockerfile
FROM python:3.9-alpine

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 5000
CMD ["python", "app.py"]

```
This Dockerfile sets up a Python 3.9 Alpine image, copies our application files to the /app directory, installs the required Python packages, and sets the command to run our Flask application.

Finally, create a new file named requirements.txt with the following contents:

``` makefile
Flask==2.1.0
```
This file lists the required Python packages for our application.

Build the Docker image by running the following command in the directory with the Dockerfile and requirements.txt files:

``` bash
docker build -t myapp:latest .
```

This will build a Docker image with the tag 

> myapp:latest.

## Create Kubernetes resources

Now that we have a Docker image for our application, we need to create a Kubernetes manifest that describes how to deploy our application to the cluster. Create a new file named deployment.yaml with the following contents:

``` yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  selector:
    matchLabels:
      app: myapp
  replicas: 1
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: myapp:latest
        imagePullPolicy: Never
        ports:
        - containerPort: 5000 # change this if your flask app uses a different port
```
This manifest describes a Kubernetes deployment named myapp that runs one replica of our myapp container. The selector field specifies that this deployment should manage all pods with the label app=myapp. The template field describes the pod template for this deployment, including the container specification for our myapp container.

We've created a deployment that manages a single replica of our application, but we need a way to expose that application to the network so that users can access it. We'll create a Kubernetes service to do this. Create a new file named service.yaml with the following contents:

``` yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp-service # you can name this whatever you want
  labels:
    app: myapp
spec:
  selector:
    app: myapp # this should match the label of your deployment pod
  ports:
    - protocol: TCP 
      port: 80 # this is the port that will be used by the ingress controller 
      targetPort: 5000 # this should match the container port of your deployment pod
```

This manifest describes a Kubernetes service named myapp that exposes port 80 on all nodes in the cluster, and forwards traffic to port 5000 on the myapp pods. The selector field specifies that this service should target all pods with the label app=myapp.

To expose the service to the external world - you need a resource of type ingress. The default ingress controller in k3d is [traefik](https://doc.traefik.io/traefik/providers/kubernetes-ingress/)

``` yaml
apiVersion: networking.k8s.io/v1
kind: Ingress 
metadata:
  name: myapp-ingress # you can name this whatever you want 
spec:
  rules:
    - host: myapp.local # this is the hostname for your ingress 
      http:
        paths:
          - pathType : Prefix # added pathType
            path : / # this means any path starting with / will be routed to your service 
            backend :
              service : # added service field
                name : myapp-service # this should match the name of your service 
                port : 
                  number : 80 # this should match the port of your service 
```

Before you can go on to the next step, you need to import the image you just built, to the cluster. To do this - you need to run the following:

``` bash
k3d image import myapp:latest -c yadoc-exposed
```

Deploy the manifests: We've created two Kubernetes manifests, deployment.yaml, service.yaml, ingress.yaml that describe how to deploy our application to the cluster. We can deploy these manifests by running the following command:

``` bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml
```
This commands will create the deployment and service resources in the Kubernetes cluster. You can check the status of the deployment by running 
``` bash
kubectl get deployments 
```
and the status of the service by running 

``` bash
kubectl get services
```
to get the status of the ingress:

``` bash
kubectl get ing
```

Once the deployment and service are both in a Running state, and you are seeing IPs assigned to your ingress you should be able to access the application. Small note: you will need to edit your 

``` bash
/etc/hosts
```

file and add the following line:

``` bash
127.0.0.1        myapp.local
```

Then you should be able to confirm that your app is running by going to http://myapp.local:8081/ using your favourite browser.


## Congratulations, you deployed your first app on kubernetes!

>____________________________


# Lesson 2

All is fun and dandy but we need to make this interesting. Kubernetes is a powerful tool and it can do so much more than just static deployments. It can intelligently scale your deployments to match the demand your application is experiencing. Introducing [Horizontal Pod Autoscaler](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)

In case you were too lazy to follow the above link - here is some introduction about HPA: it is a Kubernetes feature that automatically adjusts the number of replicas of a pod based on the current demand for the application. In other words, it automatically scales the number of running pods up or down based on the observed CPU utilization, memory usage, or other custom metrics.

The HPA controller is responsible for monitoring the resource utilization of a set of pods, and based on the defined policies, it determines whether to increase or decrease the number of replicas to meet the target resource utilization. The HPA controller can use different metrics to determine the required scale, such as CPU usage, memory utilization, or custom metrics that are specific to the application.

To use HPA, you need to define a Kubernetes resource called HPA, which specifies the scaling policy. You can set the minimum and maximum number of replicas, the target CPU or memory utilization, and other parameters. Once the HPA is created, the controller monitors the pods and automatically adjusts the number of replicas to meet the desired utilization.

HPA is useful for handling sudden spikes in traffic and load on an application. It ensures that there are enough resources available to handle the increased demand, and scales down the resources when the load decreases. This helps in optimizing resource utilization and reducing costs, as the resources are only used when needed. Additionally, HPA can be used with Kubernetes cluster autoscaling, which automatically adds or removes nodes to handle the increased demand for the application.

In the spirit of continuity - we will build our next practical lesson on the previous one, with slight changes:

## Create a k3d cluster

Open up a terminal window and create a new k3d cluster:
   
``` bash
k3d cluster create yadoc-exposed -p "8081:80@loadbalancer" --agents 3

```

> **Note:** If you still have the old cluster running, the one from lesson 1 - I would go ahead and delete it, so that the resources from lesson 1 do not interfere with the ones from this lesson. You can do this with 

``` bash
k3d cluster delete yadoc-exposed
```

## Create a namespace

In lesson #1 I did not want to bore you with too many kubernetes concepts so we did not go over the concept called [namespaces](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/). A namespace is a logical partition within a cluster that allows users to organize resources, control access, and provide isolation. It provides a way to divide a single Kubernetes cluster into multiple virtual clusters, with each namespace containing its own resources such as pods, services, and replica sets.

By default, Kubernetes has a "default" namespace which is where resources are created if no namespace is specified. However, namespaces are useful for larger clusters or when multiple teams or applications are running in the same cluster, as they allow for better organization, control and isolation of resources.

This is what we used in lesson #1 - we did not specify any namespace for any of the resources we created, so they were created in the "default" namespace. Going forward we will be avoiding this. 

``` bash
kubectl create ns hpa-test
```

But I am getting ahead of myself. First, we need to:


## Write and containerize a flask app that will serve a text file

In order to test HPA we will deploy to our cluster a flask app that serves a txt file, we will make that file around 10Mb and then fire up a bunch of requests to get that file, thus trying to overload the app and make it scale up. Without further ado - here is our app.py that serves the test.txt file from our root filesystem:

``` python
from flask import Flask, send_file

app = Flask(__name__)

@app.route('/')
def serve_file():
    return send_file('test.txt')

if __name__ == '__main__':
    app.run()
```

here is our Dockerfile:

``` bash
# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

# Expose port 8000 for the Flask app to listen on
EXPOSE 5000

# Set the default command to start the Flask app using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

> **Note** you might want to read about [gunicorn](https://gunicorn.org/#docs)

Please note the change in the requirements.txt file:

``` bash
Flask==2.1.0
gunicorn==20.1.0
```

Next - we need to build our image using:

``` bash
docker build -t myapp:hpa-test .
```

Don't forget to import the image to the k3d cluster:

``` bash
k3d image import myapp:hpa-test -c yadoc-exposed
```

The above will create the following image:

``` bash
myapp:hpa-test
```

## Create the kubernetes resources

There are no big changes to the service.yaml and ingress.yaml files, besides the fact that all their manifests are namespaced i.e. have this line in their metadata section:

``` yaml
namespace: hpa-test
```

We have some more changes in our deployment.yaml:

``` yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  namespace: hpa-test
spec:
  selector:
    matchLabels:
      app: myapp
  replicas: 1
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: myapp:hpa-test
        imagePullPolicy: Never
        ports:
        - containerPort: 5000 # change this if your flask app uses a different port
        resources:
          requests:
            cpu: "50m"
            memory: "50Mi"
          limits:
            cpu: "100m"
            memory: "100Mi"
```

Notice the "resources" part under spec.containers? This is used to specify the CPU and MEM resources that the pods governed by this deployment can have. Read more about the difference betweeen requests and limits [here](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/), but basically - requests is the minimum that this pod can get and the limits is.. well - the maximum, or the limit. Having this in our deployment.yaml also ensures that the relevant metrics will be sent to the kubernetes metrics server and HPA will be able to actio on these metrics readings.

hpa.yaml:

``` yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: myapp-hpa
  namespace: hpa-test
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  minReplicas: 1
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 60
```
Now there are a couple of interesting parts in the above manifest. First:

``` yaml
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  minReplicas: 1
  maxReplicas: 10
```

We are telling this HPA that our targe deployment is called myapp and the range for the number of replicas (pods) is between 1 and 10. 

Second one is:

``` yaml
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 60
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 60
```

We are telling HPA that whenever CPU or MEM utilization reaches 60% - we want the deployment to scale up. 

Now let's apply the manifests:

``` bash
kubectl apply -f deployment.yaml
kubectl apply -f hpa.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml
```

We can make sure that the pod(s) are up and running with this command:

``` bash

kubectl get pods -n hpa-test

```

We should get something similar to this:

``` bash
grclm@grclm:~$ kubectl get pods -n hpa-test
NAME                     READY   STATUS    RESTARTS   AGE
myapp-56488c97b9-5hlpr   1/1     Running   0          41m
myapp-56488c97b9-5tnzj   1/1     Running   0          41m
```

Our app should be available under http://myapp.local:8081/ (given that you did not change anything to the /etc/hosts file). You should be seeing it serving the contents of the test.txt file directly on the webpage.

## Testing the HPA:

### Observing the logs:

It's always fun to read the logs and see what's happening under the hood. For this exercise we can take a look at 3 things (I opened 3 separate terminal windows and placed them all on a single screen to see this in realtime):

- kubernetes events:
  
  ``` bash
  kubectl get events -n hpa-test --watch
  ```
- description of the hpa resource:
  ``` bash
  kubectl describe hpa myapp-hpa -n hpa-test
  ```
- monitor the number of pods:
  ``` bash
  kubectl get pods -n hpa-test --watch

Now go to http://myapp.local:8081/ and start hitting the refresh button (it's F5 in most of the browsers). 

- You should start seeing the number of pods increasing
- You should see similar messages in the events:
  ``` bash
  0s          Normal    SuccessfulRescale              horizontalpodautoscaler/myapp-hpa   New size: 8; reason: memory resource utilization (percentage of request) above target
  0s          Normal    ScalingReplicaSet              deployment/myapp                    Scaled up replica set myapp-56488c97b9 to 8 from 6
  0s          Normal    SuccessfulCreate               replicaset/myapp-56488c97b9         Created pod: myapp-56488c97b9-7qznt
  ```
- You should see the following when you describe the HPA:
  ``` bash
  Normal   SuccessfulRescale             11m   horizontal-pod-autoscaler  New size: 2; reason: cpu resource utilization (percentage of request) above target
  Normal   SuccessfulRescale             42s   horizontal-pod-autoscaler  New size: 3; reason: memory resource utilization (percentage of request) above target
  Normal   SuccessfulRescale             12s   horizontal-pod-autoscaler  New size: 4; reason: memory resource utilization (percentage of request) above target
  ```

## Congratulations, you autoscaled your first app on kubernetes!

# Lesson 3

Let's talk Kubernetes architecture. By this time I would assume you already tried googling some stuff and you might have gained a pretty good understanding of what Kubernetes is and what does it do, how is it useful and what are it's capabilities. If you would still like to read my take on Kubernetes architecture then please, read on:

## Architecture

Kubernetes is an open-source container orchestration platform that is designed to automate the deployment, scaling, and management of containerized applications. At its core, Kubernetes is composed of a set of distributed components that work together to provide a powerful and scalable platform for running containerized workloads.

The Kubernetes architecture consists of two main components: the Control Plane and the Worker Nodes. The Control Plane manages the overall state of the cluster and makes decisions about scheduling and scaling workloads, while the Worker Nodes are responsible for running the containers that make up the workloads.

The Control Plane consists of several components, including the API Server, etcd, the Controller Manager, and the Scheduler. These components work together to provide a centralized management plane for the Kubernetes cluster.

The Worker Nodes are responsible for running the containerized workloads and consist of several components, including the Kubelet, Container Runtime, and kube-proxy.

### Control Plane

#### **API Server**

The API Server is a critical component of the Control Plane in Kubernetes. It provides a central point of management for the Kubernetes cluster by exposing an API that allows administrators to manage the resources in the cluster. The API Server is designed to be highly available and scalable, and it can be run in a distributed configuration to provide fault tolerance and high availability. 

Let's have some fun with the API server of our test cluster

Create the k3d cluster 

``` bash

k3d cluster create yadoc-api-exposed --api-port 6550 -p "8081:80@loadbalancer" --agents 3
```

>NOTE --api-port 6550 is used to have k3s‘s API-Server listening on port 6550 with that port mapped to the host system. That means you can access the API server using https://0.0.0.0:6550/

View your kubeconfig file authentication data:

``` bash

cat .kube/config
```

You will see the following fields:

``` yaml
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: cert_auth_data
    server: https://0.0.0.0:6550
  name: k3d-yadoc-api-exposed
contexts:
- context:
    cluster: k3d-yadoc-api-exposed
    user: admin@k3d-yadoc-api-exposed
  name: k3d-yadoc-api-exposed
current-context: k3d-yadoc-api-exposed
kind: Config
preferences: {}
users:
- name: admin@k3d-yadoc-api-exposed
  user:
    client-certificate-data: client_cert_data
    client-key-data: clien_key_data

```

Parse the ./kube/config to output the contents of the certificates to the respective files:

``` bash

(yq e '.clusters[0].cluster."certificate-authority-data"' ~/.kube/config | base64 --decode) > cert_auth_data.crt

(yq e '.users[0].user."client-certificate-data"' ~/.kube/config | base64 --decode) > client_cert_data.crt

(yq e '.users[0].user."client-key-data"' ~/.kube/config | base64 --decode) > client_key_data.key

```


You can use the files created by parsing this kubeconfig file to populate the api request that we are going to construct:

``` bash

curl --cacert cert_auth_data.crt --cert client_cert_data.crt --key client_key_data.key https://0.0.0.0:6550/api/v1/namespaces/default/pods
```

Now let's test all of this. First - create a namespace, then run a pod inside that namespace:

``` bash

kubectl create ns api-test

kubectl run nginx -n api-test --image=nginx:latest

```

Check that the pods is running and then output it's yaml manifest:

``` bash
kubectl get pods -n api-test

kubectl get pod nginx -n api-test -o=yaml

```

Let's try to look for some recognizable information in this pod yaml manifest:

``` bash
kubectl get pod nginx -n api-test -o=yaml | grep volumes -C 1
```

Take note of the output. In my case it was:

```
    tolerationSeconds: 300
  volumes:
  - name: kube-api-access-wcl8p
```

Fire the API request from the above and replace the namespace with "api-test" and grep for "volumes"

``` bash
curl --cacert cert_auth_data.crt --cert client_cert_data.crt --key client_key_data.key https://0.0.0.0:6550/api/v1/namespaces/api-test/pods | grep volumes -C 2
```

I got this:

``` bash
{
            "name": "kube-api-access-wcl8p",
```

There you go, you just sent an API request to your k3d cluster, congrats!


The API Server is responsible for several key functions, including:

1. Authenticating and Authorizing Requests: The API Server authenticates and authorizes all requests to the Kubernetes API. It verifies that the request is coming from a valid source and that the user making the request has the necessary permissions to access the requested resource.

2. Request Processing: The API Server processes all requests to the Kubernetes API. It handles requests to create, modify, and delete resources in the cluster, and it ensures that the desired state of the cluster is maintained.

3. Resource Validation: The API Server validates all requests to the Kubernetes API to ensure that they conform to the expected schema and data format. It also enforces any constraints or policies that are in place to ensure the security and stability of the cluster.

4. State Management: The API Server is responsible for managing the overall state of the Kubernetes cluster. It keeps track of the state of all resources in the cluster and ensures that the desired state of the cluster is maintained.

The API Server is typically deployed as a highly available component in a Kubernetes cluster. It can be run in a replicated configuration to provide fault tolerance and high availability. When a request is made to the API Server, it is load balanced across the available instances of the API Server to ensure that the request is handled by a healthy instance.

In summary, the API Server is a critical component of the Kubernetes Control Plane. It provides a central point of management for the Kubernetes cluster and is responsible for authenticating and authorizing requests, processing requests, validating resources, and managing the overall state of the cluster.

#### **etcd**

etcd is a distributed key-value store that is used to store the configuration and state information for a Kubernetes cluster. It is a critical component of the Control Plane in Kubernetes and is used to maintain the overall state of the cluster.

etcd provides a highly available and scalable storage solution for the Kubernetes cluster. It is designed to be highly fault-tolerant and can withstand failures of individual nodes or even entire clusters without losing data. This makes it an ideal storage solution for the critical configuration and state information needed to run a Kubernetes cluster.

By default, k3d clusters don't use etcd. If we want to force k3d to create a cluster with etcd, we have to run:

``` bash

k3d cluster create yadoc-with-etcd --api-port 6551 -p "8082:80@loadbalancer" --agents 3 --k3s-arg "--cluster-init@server:0"


etcd is used by several components in the Kubernetes Control Plane, including the API Server, the Controller Manager, and the Scheduler. These components use etcd to store configuration and state information, such as the desired state of the cluster, the state of individual nodes, and the status of workloads running in the cluster.

When a change is made to the state of the Kubernetes cluster, such as creating a new Pod or updating a Service, the API Server writes the updated state to etcd. The other components in the Control Plane then read this state from etcd to determine the actions they need to take to ensure that the desired state of the cluster is maintained.

etcd is typically deployed as a cluster of nodes, with each node running a copy of the etcd software. The nodes communicate with each other to ensure that the state of the cluster is consistent across all nodes, and the cluster can continue to function even if individual nodes fail.

In summary, etcd is a distributed key-value store that is used to store the configuration and state information for a Kubernetes cluster. It provides a highly available and fault-tolerant storage solution for the critical information needed to run a Kubernetes cluster.

#### **Controller Manager**

The Controller Manager is a critical component of the Control Plane in Kubernetes. It is responsible for managing the various controllers that are used to ensure that the desired state of the cluster is maintained.

Controllers are responsible for monitoring the state of various resources in the cluster and taking action to ensure that the desired state is maintained. For example, the ReplicaSet controller ensures that the specified number of replicas of a particular Pod are running in the cluster, while the Service controller ensures that the network endpoints for a particular Service are correctly configured.

The Controller Manager runs several different controllers to manage different resources in the Kubernetes cluster. These controllers include the Node controller, the Service Account and Token controller, the Namespace controller, and many others.

The Controller Manager is responsible for starting and stopping these controllers as needed, and it monitors the health of each controller to ensure that they are running correctly. It also provides a central point of management for these controllers, allowing administrators to view the status of each controller and make any necessary configuration changes.

The Controller Manager uses etcd to store the state information for each controller. When a controller detects a change in the state of a resource, it updates the state information in etcd. The Controller Manager then reads this state information from etcd to determine the actions that need to be taken to ensure that the desired state of the cluster is maintained.

In summary, the Controller Manager is a critical component of the Kubernetes Control Plane. It is responsible for managing the various controllers that are used to maintain the desired state of the cluster. It provides a central point of management for these controllers and uses etcd to store the state information for each controller.

#### **Scheduler**

The Scheduler is another critical component of the Control Plane in Kubernetes. Its primary responsibility is to schedule Pods onto Nodes in the cluster based on a variety of factors, such as resource availability, quality of service requirements, and more.

When a new Pod is created in Kubernetes, it is not immediately scheduled onto a specific Node in the cluster. Instead, the Pod is added to a queue, and the Scheduler is responsible for selecting a suitable Node for the Pod to run on.

The Scheduler selects a suitable Node for the Pod by evaluating a set of rules and constraints that are defined by the Pod's specification, such as CPU and memory requirements, affinity and anti-affinity rules, and others. It also considers the current state of the cluster, including the available resources on each Node and any resource constraints that may be in place.

Once the Scheduler has selected a suitable Node for the Pod, it updates the Pod's specification to reflect the selected Node. The Pod is then scheduled to run on that Node, and the Scheduler monitors the state of the Pod to ensure that it is running correctly.

The Scheduler uses a pluggable architecture, which allows administrators to use different scheduling algorithms depending on the needs of their specific cluster. There are several different scheduling algorithms available in Kubernetes, including the default scheduling algorithm, which is a simple, priority-based algorithm that takes into account factors such as resource availability and quality of service requirements.

In summary, the Scheduler is a critical component of the Kubernetes Control Plane. It is responsible for selecting a suitable Node for each Pod in the cluster based on a variety of factors, and it uses a pluggable architecture that allows administrators to use different scheduling algorithms depending on the needs of their specific cluster.

### Worker Nodes

#### **kubelet**

kubelet is an agent that runs on each Node in the Kubernetes cluster. Its primary responsibility is to ensure that the Pods running on that Node are running correctly and to report their status back to the Control Plane.

When a new Pod is scheduled onto a Node in the cluster, the kubelet on that Node is responsible for ensuring that the containers in the Pod are running correctly. It does this by communicating with the container runtime, such as Docker or containerd, to start the containers and monitor their state.

The kubelet also monitors the health of the Pods running on the Node. It periodically checks the status of the containers in each Pod and reports any issues back to the Control Plane. If a container or Pod becomes unhealthy, the kubelet will take corrective action, such as restarting the container or rescheduling the Pod onto a different Node in the cluster.

The kubelet also manages the networking for the Pods running on the Node. It ensures that each Pod has a unique IP address and that the network connectivity between the Pods on the Node is correctly configured.

In addition, the kubelet is responsible for communicating with the Control Plane to provide information about the state of the Node and the Pods running on it. It provides information such as the amount of available resources on the Node, the status of the containers in each Pod, and more.

Overall, kubelet is a critical component of the Kubernetes cluster. It is responsible for ensuring that the Pods running on each Node are running correctly and reporting their status back to the Control Plane. It manages the networking for the Pods and communicates with the Control Plane to provide information about the state of the Node and the Pods running on it.

#### **kube-proxy**

kube-proxy is another critical component of the Kubernetes cluster. Its primary responsibility is to manage the networking for Services in the cluster.

In Kubernetes, a Service is an abstraction that defines a logical set of Pods and a policy by which to access them. Services provide a stable IP address and DNS name that can be used to access the Pods, even if they are moved or replaced.

When a Service is created in Kubernetes, kube-proxy is responsible for configuring the network routing to ensure that traffic to the Service is correctly load-balanced across the Pods that are backing it.

kube-proxy works by running on each Node in the cluster and maintaining a set of network rules that define how traffic should be routed to the Pods. It uses a variety of techniques to ensure that the routing rules are correctly updated as Pods are created, moved, or deleted.

One of the techniques used by kube-proxy is IP tables. kube-proxy maintains a set of IP tables rules that are used to route traffic to the Pods. When a new Service is created, kube-proxy creates a set of IP tables rules that forward traffic to the Pods that are backing the Service. If a Pod is deleted or moved, kube-proxy updates the IP tables rules to reflect the new state of the cluster.

kube-proxy can also be configured to use other networking modes, such as IPVS, which is a more efficient and scalable way to manage network routing for large clusters.

Overall, kube-proxy is a critical component of the Kubernetes cluster. It is responsible for managing the networking for Services in the cluster and ensuring that traffic is correctly load-balanced across the Pods that are backing them. It uses a variety of techniques, such as IP tables and IPVS, to ensure that the network routing rules are correctly updated as the state of the cluster changes.

#### **Container Runtime**

A container runtime is a software that is responsible for managing the containers that run on a Node in the Kubernetes cluster. In other words, it is the component that actually runs the containers and provides isolation between them.

Kubernetes supports a variety of container runtimes, including Docker, containerd, and CRI-O. Each of these runtimes provides a different set of features and capabilities, but they all perform the same basic functions:

1. Image management: The container runtime is responsible for pulling container images from a container registry, such as Docker Hub or the Google Container Registry, and storing them on the Node's local disk.

2. Container lifecycle management: The container runtime starts, stops, and restarts containers in response to requests from the Kubernetes API server or the kubelet running on the Node.

3. Networking: The container runtime provides networking capabilities for the containers running on the Node, such as assigning IP addresses to the containers and managing the network interfaces.

4. Storage: The container runtime provides storage capabilities for the containers running on the Node, such as mounting volumes and managing persistent storage.

5. Security: The container runtime provides security features to ensure that containers are isolated from each other and from the host system. This includes features such as user namespaces, seccomp profiles, and AppArmor profiles.

In summary, the container runtime is a critical component of the Kubernetes cluster. It is responsible for managing the containers that run on a Node, including image management, container lifecycle management, networking, storage, and security. The choice of container runtime depends on the specific needs of the organization and the features provided by each runtime.

>sample diagram

```mermaid
graph LR
A[Square Rect] -- Link text --> B((Circle))
A --> C(Round Rect)
B --> D{Rhombus}
C --> D
