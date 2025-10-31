#!/usr/bin/env python3
import grpc
import jobs_pb2
import jobs_pb2_grpc
import time
import argparse
import logging
import sys
import re
from collections import Counter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Engine:
    def __init__(self, engine_id, role, capacity, coordinator_address):
        self.engine_id = engine_id
        self.role = role
        self.capacity = capacity
        self.coordinator_address = coordinator_address
        self.channel = None
        self.stub = None
        
    def connect(self):
        """Connect to coordinator"""
        try:
            self.channel = grpc.insecure_channel(self.coordinator_address)
            self.stub = jobs_pb2_grpc.JobServiceStub(self.channel)
            logger.info(f"Connected to coordinator at {self.coordinator_address}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    def register(self):
        """Register with coordinator"""
        try:
            request = jobs_pb2.RegisterEngineRequest(
                engine_id=self.engine_id,
                role=self.role,
                capacity=self.capacity
            )
            response = self.stub.RegisterEngine(request)
            
            if response.success:
                logger.info(f"Registered successfully: {response.message}")
                return True
            else:
                logger.error(f"Registration failed: {response.message}")
                return False
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False
    
    def process_map_task(self, task):
        """Process a map task - count word frequencies"""
        logger.info(f"Processing map task: job={task.job_id}, shard={task.shard_id}")
        
        # Extract words and count
        words = re.findall(r'\b\w+\b', task.text_content.lower())
        word_counts = Counter(words)
        
        # Create map outputs
        outputs = []
        for word, count in word_counts.items():
            outputs.append(jobs_pb2.MapOutput(word=word, count=count))
        
        logger.info(f"Map task complete: {len(word_counts)} unique words")
        return outputs
    
    def process_reduce_task(self, task):
        """Process a reduce task - sum counts for a word"""
        logger.info(f"Processing reduce task: job={task.job_id}, word={task.word}")
        
        total_count = sum(task.counts)
        
        logger.info(f"Reduce task complete: word={task.word}, total={total_count}")
        return total_count
    
    def fetch_and_process(self):
        """Fetch a task and process it"""
        try:
            request = jobs_pb2.FetchJobRequest(engine_id=self.engine_id)
            response = self.stub.FetchJob(request)
            
            if response.task_type == "none":
                return False
            
            if response.task_type == "map":
                task = response.map_task
                outputs = self.process_map_task(task)
                
                # Report result
                report = jobs_pb2.ReportResultRequest(
                    engine_id=self.engine_id,
                    job_id=task.job_id,
                    task_type="map",
                    shard_id=task.shard_id,
                    map_outputs=outputs
                )
                self.stub.ReportResult(report)
                logger.info(f"Reported map result for job={task.job_id}")
                return True
            
            elif response.task_type == "reduce":
                task = response.reduce_task
                total = self.process_reduce_task(task)
                
                # Report result
                report = jobs_pb2.ReportResultRequest(
                    engine_id=self.engine_id,
                    job_id=task.job_id,
                    task_type="reduce",
                    word=task.word,
                    total_count=total
                )
                self.stub.ReportResult(report)
                logger.info(f"Reported reduce result for job={task.job_id}")
                return True
        
        except grpc.RpcError as e:
            logger.error(f"RPC error: {e}")
            return False
        except Exception as e:
            logger.error(f"Processing error: {e}")
            return False
    
    def run(self):
        """Main engine loop"""
        logger.info(f"Starting engine {self.engine_id} as {self.role}")
        
        while True:
            # Connect if not connected
            if not self.channel:
                if not self.connect():
                    logger.warning("Retrying connection in 5 seconds...")
                    time.sleep(5)
                    continue
                
                if not self.register():
                    logger.warning("Retrying registration in 5 seconds...")
                    time.sleep(5)
                    self.channel = None
                    continue
            
            # Fetch and process task
            try:
                had_work = self.fetch_and_process()
                
                if not had_work:
                    time.sleep(2)  # Wait before fetching again
                else:
                    time.sleep(0.5)  # Small delay between tasks
            
            except KeyboardInterrupt:
                logger.info("Shutting down engine...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(5)
                self.channel = None

def main():
    parser = argparse.ArgumentParser(description='MapReduce Engine Worker')
    parser.add_argument('--engine-id', required=True, help='Unique engine ID')
    parser.add_argument('--role', required=True, choices=['mapper', 'reducer'], help='Engine role')
    parser.add_argument('--capacity', type=int, default=5, help='Task capacity')
    parser.add_argument('--coordinator', default='localhost:50051', help='Coordinator address')
    
    args = parser.parse_args()
    
    engine = Engine(
        engine_id=args.engine_id,
        role=args.role,
        capacity=args.capacity,
        coordinator_address=args.coordinator
    )
    
    engine.run()

if __name__ == '__main__':
    main()
