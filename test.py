
import os
import logging
import requests
import time
from datetime import datetime
from html import escape
from locust import HttpUser, TaskSet, task, web, between, events


class WebsiteUser(HttpUser):
    wait_time = between(5, 15)
    
    @task
    def index(self):
        self.client.get("/")




stats = {}
path = "/tmp"



@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    if environment.web_ui:
        time.sleep(3)
        s = environment.stats.total
        send_stats_to_pushgateway(s)
        if environment.stats.total.fail_ratio > 0.1:
            logging.error("Test failed due to failure ratio > 10%")
            environment.process_exit_code = 1
        else:
            environment.process_exit_code = 0
        
def _submit_wrapper(job_name, metric_name, metric_value):
    headers = {'X-Requested-With': 'Python requests', 'Content-type': 'text/xml'}
    requests.post('http://%s/metrics/job/%s' % (os.environ['PROM_PUSHGATEWAY'], job_name),
                  data='%s %s\n' % (metric_name, metric_value), headers=headers)

        
def send_stats_to_pushgateway(stats):
    arr = stats.percentile()
    resp_per = arr.split()
    resp_per = resp_per[1:-1]
    num_requests = str(stats.num_requests)
    num_failures = str(stats.num_failures)
    target_per = resp_per[4]
    rps = stats.total_rps

    jobname = os.environ['PROM_JOBNAME']
    
    _submit_wrapper(jobname, 'locust_total_requests', num_requests)
    _submit_wrapper(jobname, 'locust_total_failures', num_failures)
    _submit_wrapper(jobname, 'locust_90th_percentile', target_per)
    _submit_wrapper(jobname, 'locust_requests_per_second', str(rps))   
        
