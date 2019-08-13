# Gcloud task queue
Link: https://cloud.google.com/tasks/docs/creating-queues

## Command lines commands:

### Create
```
gcloud tasks queues create [QUEUE_ID]
```

### Describe
```
gcloud tasks queues describe [QUEUE_ID]
```

### Update
```
gcloud tasks queues update [QUEUE_ID] \
    --routing-override=service:[SERVICE]
```

Check this out for retries policies:
https://stackoverflow.com/questions/46979539/handling-failure-after-maximum-number-of-retries-in-google-app-engine-task-queue