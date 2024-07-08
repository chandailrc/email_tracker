import asyncio
import time

# Define a synchronous function
def sync_task(n):
    print(f"Starting sync task with n={n}")
    time.sleep(5)
    print(f"Finished sync task with n={n}, result={result}")


# Define an asynchronous function to run the sync task in a thread
async def async_task(n):
    loop = asyncio.get_event_loop()
    await asyncio.to_thread(sync_task, n)


# Define an asynchronous function for Task 1
async def task1():
    print("Task 1: Step 1")
    await asyncio.sleep(1)  # Simulate waiting for 1 second
    await async_task(1000000)  # Call the async version of the sync task
    print("Task 1: Step 2")

# Define an asynchronous function for Task 2
async def task2():
    print("Task 2: Step 1")
    await asyncio.sleep(2)  # Simulate waiting for 2 seconds
    await async_task(2000000)  # Call the async version of the sync task
    print("Task 2: Step 2")

# Define the main function that runs both tasks concurrently
async def main():
    # Create two tasks
    task1_coroutine = task1()
    task2_coroutine = task2()

    # Run both tasks concurrently
    await asyncio.gather(task1_coroutine, task2_coroutine)

# Run the main function
def runmain():
    asyncio.run(main())
