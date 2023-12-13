# Log data Extraction

⚠️ **The data extraction approach available on this repository is done through the [Logstash](https://www.elastic.co/logstash/) tool**

With this Logstash configuration you can extract the OutSystems monitoring data by:
* Pulling data directly from OutSystems DB, in particular from [Log Tables](https://success.outsystems.com/Documentation/11_x_platform/Managing_the_Applications_Lifecycle/Monitor_and_Troubleshoot/Logging_database_and_architecture)
  * See more at: [Logstash data pipelines/Monitor Probe](Logstash/pipelines/database)
* Pulling data through an OutSystem application that exposes the majority of the data was REST endpoints that then can be consumed.
  * The application it's available in [OutSystems Forge](https://www.outsystems.com/forge/), it's [Monitor Probe](https://www.outsystems.com/forge/component-overview/4559/monitorprobe)
    * See more at: [Logstash data pipelines/Monitor Probe](Logstash/pipelines/monitor-probe)

Both approaches will work for Cloud and On-premises hosted Outsystems

# Installing Logstash

## Ensuring Linux is up to date

First of all, you should [make sure Linux is up to date](Ensuring-Linux-is-up-to-date.md).

## Installing Logstash
We recommend installing Logstash from the [package repository](https://www.elastic.co/guide/en/logstash/current/installing-logstash.html#package-repositories) following the latest approach for your system

Logstash is not started automatically after installation. Starting and stopping Logstash depends on the init system of the underlying operating system.

You will need to navigate to various directories during the configuration of this setup, please use the [following page](https://www.elastic.co/guide/en/logstash/8.11/dir-layout.html#dir-layout) as reference for the Directory structure of Logstash for your setup

## Setting up the service for automatic start

Now the information about services must be **reloaded** and the new service must be **enabled**.

`sudo /bin/systemctl daemon-reload`  

`sudo /bin/systemctl enable logstash.service`  

## Starting the service

After the installation is done, the service must be started.  

Ubuntu/Debian:

`sudo service logstash start`  

Red Hat/CentOS:

`sudo systemctl start logstash`  

## Checking the service

During troubleshooting, it can be necessary to check the status of the service.

Ubuntu/Debian:

`sudo service logstash status`

Red Hat/CentOS:

`sudo systemctl status logstash`

Using CURL:

`sudo curl -XGET "localhost:9600"`  

## Stopping the service

In case of maintenance, it can be necessary to stop the service.

Ubuntu/Debian:

`sudo service logstash stop`

Red Hat/CentOS:

`sudo systemctl stop logstash`  

## Installing Logstash Plugins

There are 4 kinds of Logstash plugins which are used by this project:
* Input Plugins 
* Filter Plugins 
* Output Plugins
* Codec Plugins

Because new plugins we will be using use these libraries please make sure you are running the latest versions, plugins should be up to date before installing new ones.

### Update existing plugins
Please make sure to stop the Logstash service and run the following command (as root):
**Debian based systems**
`/etc/default/logstash/bin/logstash-plugin update`  

**Red Hat based systems**
`/usr/share/logstash/bin/logstash-plugin update`  

:warning:**Important Notes**
* Sometimes as new versions of Logstash are released the [directory changes]((https://www.elastic.co/guide/en/logstash/8.11/dir-layout.html#dir-layout) ). Currently, for Logstash 7 and 8, the full command is : `/usr/share/logstash/bin/logstash-plugin update`
* If you don't know where the file is located, you can run: `find / -name logstash-plugin`

<br>

### Installing other need plugins
It is mandatory to install Filter-Range plugin and the Dynatrace output plugin. 

please make sure Logstash is stopped and run the following command (as root):
**Debian based systems**
`/etc/default/logstash/bin/logstash-plugin install logstash-filter-range`  
`/etc/default/logstash/bin/logstash-plugin install logstash-output-dynatrace`

**Red Hat based systems**
`/usr/share/logstash/bin/logstash-plugin install logstash-filter-range`  
`/usr/share/logstash/bin/logstash-plugin install logstash-output-dynatrace`

## Relevant information
Everything you need to know about Logstash Plugins can be found in [Logstash Official Page](https://www.elastic.co/guide/en/logstash/current/index.html).
