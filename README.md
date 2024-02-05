# Outsystems Dynatrace Log Integration

## About 📑
This repository contains templates to provide better and faster insights on top of [OutSystems](https://www.outsystems.com/) monitoring data.

These templates are seperated into :
- **Documentation**
    - Explaination of different ways to [extract data](Documentation/Access-Monitoring-Data.md) out of Outsystems 
    - Different types of [monitoring data](Documentation/Monitoring-Data.md) provided by Dynatrace Agents and Outsystems 
- **Logstash pipelines**
    :exclamation: For Outsystems 11 we advice to use [log streaming](https://success.outsystems.com/documentation/11/managing_the_applications_lifecycle/monitor_and_troubleshoot/introduction_to_log_streaming/) instead of Logstash
    - Simplify the ETL of monitoring data from the OutSystems platform.
    - Enrich data to allow building more human-readable visualizations.
- **Dynatrace dashboards**
    - Provide an out-of-the-box set of visualizations that help understand OutSystems applications and platform health, based on their performance and errors.
    - Reduce time to insights (based on OutSystems monitoring data).
    - Improve troubleshooting capabilities.

<br>

Example of one of the visualizations available on this repository:
![examples](Dashboards/images/)

<br>

:exclamation: To know how to set up and use this repository artifacts you can go directly to the this section [How to use the contents of this repository](#how-to-use-the-contents-of-this-repository)

:exclamation: **Want to support to implement or extend this assets?**
Contact Dynatrace Professional Services. You can know more about us at:
https://www.dynatrace.com/services-support/#dynatrace-services/ 
  
<br>

## Goal 🎯
The major goal of these accelerators is to provide OutSystems customers with an out-of-the-box solution to:
- Easily **observe the OutSystems monitoring data on Dynatrace with more advanced visualizations, Unified Observability and Easy automation**, compared to the cababilites from the built-in tools of the OutSystems platform.
- Easily search through OutSystems monitoring data, in particular through the OutSystems logs with Dynatrace Query Lanquage (DQL)
- Retain logs for up to 10 Years
- **Do more advanced monitoring**, compared to what can be done using the built-in tools of the OutSystems platform. Things like:
    - Build alerts for an OutSystems environment or OutSystems Factory.
    - Leverage Dynatrace Davis AI capabilities to have deeper insights on performance and behavior of applications, and the platform itself.
    - Build quality gates with Dynatrace Site Reliabilty Guardians
    - Start automating releases driven by Dynatrace workflows
    - Intergrate log data with Outsystems applications by levering Workflow API's
- **Observe OutSystems applications performance and errors through time**.
    - Quickly pinpoint performance bottlenecks, areas to improve, etc.
    - Figure out what is affecting performance:
        - Slow Queries
        - Slow Integrations
        - Slow Extensions
- Provide an example of how to **set up and monitor SLOs**.

<br> 

## Examples of metrics can you can extract

- **Request Time Duration** (for each request):
    - Client Time (load time)
    - Server Time, which can be decomposed into:
        - SAT (Session Acquisition Time)
        - Query Execution Time
        - Integration Execution Time
        - Extension Execution Time
- **Server side performance metrics**
    - Session size
    - Viewstate size
    - Number of slow queries
    - Number of slow integrations
    - Number of slow extensions
- **Errors metrics**
    - Number of errors
    - Number of errors by type

These are just examples of some metrics that can be monitored, based on the platform log data.

<br>

## How to use the contents of this repository
If you have do not have a Dynatrace environment yet, you can start a free trial today
- [Open a Dynatrace trial](https://www.dynatrace.com/trial).

If you are all set with your Dynatrace environment you can start following these steps
1.0 [Installing Logstash](data_extraction/README.md).
2.0 [Configure Logstash](data_extraction/Logstash/README.md).


If you want to explore more deeply what you can take out of your OutSystems platform, you can refer to:
- [How to access OutSystems log data](Documentation/Access-Monitoring-Data.md).
- [Understanding monitoring data](documentation/Monitoring-Data.md).
- [Baseline metrics that OutSystems recommends to use](https://docs.google.com/spreadsheets/d/1tWQMsnxKUEGjk7-UrdKUu4X5U1koqo_M__wiigtt7g4/edit?usp=sharing)
  - Some of these metrics are built on top of OutSystems monitoring data (logs, request events, etc)

<br>


## Change log
See the change log to learn about the latest changes and improvements to this repository.
