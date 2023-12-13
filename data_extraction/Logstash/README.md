# How to use the Logstash accelerators

⚠️ **Requirements to do the configurations available on this page**
* You need to have Dynatrace ready before doing anything with the Logstash accelerators;


## About
These Logstash accelerators are in fact data pipelines that fetch monitoring data from an OutSystems environment, make a few transformations and enrichments, and load the OutSystems monitoring data into Dynatrace. 

This is possible, for now, using one of 3 ways:
1. Getting the OutSystems monitoring data directly from OutSystems logs tables of each environment through direct query (for now only usable for Microsoft SQL RDBMSs);
2. Getting the monitoring data by using the built-in [OutSystems Performance Monitoring API](https://success.outsystems.com/Documentation/11/Reference/OutSystems_APIs/PerformanceMonitoring_API);
3. Getting the OutSystems monitoring data by using Forge components like the [MonitorProbe](https://www.outsystems.com/forge/component-overview/4559/monitorprobe)


## Configure Logstash 

⚠️ **Important Note(s)**
* Before these steps, you need assure you already [installed Logstash](/data_extraction/README.md)
* And you already configured and/or updated the needed [Logastash plugins](/data_extraction/README.md#other-plugins-that-might-be-needed)

1. Read this readme fully
2. Stop the Logstash service
3. Update the Logstash config
4. Copy the pipeline config file you need
5. Edit the pipleline config
6. Copy the pattern file
7. Start the logstash service
8. Troubleshoot via Logstash logs **/var/log/logstash** if no data is send to DT 

<br>

## 3 Update the logstash config
**Review very carefully** check the standard Logstash config because the default environment variables are in that file, copy these **First** into the template and make the necessary adjustments if needed.

So, if both conditions stated in above **Important Note(s)** section are assured, first and foremost, you need to rename the file [logstash-config.txt](config/logstash-config-template.txt) to:
* For _Red Hat_ based distros: `/etc/sysconfig/logstash`
* For _Debian_ based distros: `/etc/default/logstash`

example command: `sudo cp logstash-config.txt /etc/default/logstash`

<br>

## 4 Copy the pipeline config file you need
check the [Pipeline](Logstash/pipelines) folder for the pipeline config you need.
Check the `/etc/logstash/pipelines.yml` file for the location of your config files.
Copy the config files to the location.
<br>

## 5 Edit the pipleline config
By default Logstash runs the new pipelines in serial order, however you can add multiple pipelines to the config file so they run in parallel  
but for that you need to edit configuration file `/etc/logstash/pipelines.yml` and add similar lines (adjust according to your setup):

```
- pipeline.id: devops-dev-error
  path.config: "<logstash_pipelines_folder>/db-error.conf"
- pipeline.id: devops-dev-extension
  path.config: "<logstash_pipelines_folder>/db-extension.conf"
- pipeline.id: devops-dev-integration
  path.config: "<logstash_pipelines_folder>/db-integration.conf"
- pipeline.id: devops-dev-mobile-request
  path.config: "<logstash_pipelines_folder>/db-mobile-request.conf"
```
where `<logstash_pipelines_folder>` is the folder where you've placed the pipelines from this repository.
<br>

## 6 Copy the pattern file
Copy the [pattern file](/data_extraction/Logstash/patterns) from this Repro to the location you specified in your logstash config (PATTERNS_DIR="") in step 3
<br>


> for step 7 You'll need to restart the Logstash service for these changes to take effect.
