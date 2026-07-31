# Change the number of Robots and its Distribution field in the ARGoS3 Environment 

- open ```monitoringEnvironment.argos``` (or the other .argos file) in the editor:

```xml
...
<arena size="30, 30, 1" center="0,0,0.5">

    ... 
    <!--Distribution of the SUTs (SUTX) -->
    <distribute>
      <position method="uniform" min="0,-2,0" max="3,3,0" />
      <orientation method="uniform" min="0,0,0" max="360,0,0" />
      <entity quantity="4" max_trials="100">
        <foot-bot id="SUT">
          <controller config="lrb" />
        </foot-bot>
      </entity>
    </distribute>    

    <!--Distribution of the Monitoring Robots (fb_X) -->
    <distribute>
      <position method="uniform" min="-10,-8,0" max="8,10,0" />
      <orientation method="uniform" min="0,0,0" max="360,0,0" />
      <entity quantity="20" max_trials="100">
        <foot-bot id="fb_">
          <controller config="lrb" />
        </foot-bot>
      </entity>
    </distribute> 
</arena>
...
```

- change the "min" and "max" position to set the distribution area
- change the "quantity" attribute of the entity to have more Monitoring Robots or SUTs in the Environment
- foot-bot's "id" will be increased by ARGoS automatically
- the "config" attribute of the controller has to be "lrb" to start the ROS2 Bridge for each robot