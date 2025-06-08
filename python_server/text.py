import asyncio
from time import sleep


async def print_numbers():
    for i in range(5):
        print(i)
        await asyncio.sleep(1)

async def fetch_data():
    print("Start fetching data")
    await asyncio.sleep(2)
    print("Data fetched")

async def main():
    task1 = asyncio.create_task(print_numbers())
    task2 = asyncio.create_task(fetch_data())
    await task1
    await task2

# asyncio.run(main())

'''
print:
0
Start fetching data
1
Data fetched
2
3
4
'''

async def print_numbers():
    for i in range(5):
        print(i)
        sleep(1)

async def fetch_data():
    print("Start fetching data")
    sleep(2)
    print("Data fetched")

async def main():
    task1 = asyncio.create_task(print_numbers())
    task2 = asyncio.create_task(fetch_data())
    await task1
    await task2

# asyncio.run(main())

'''
print:
0
1
2
3
4
Start fetching data
Data fetched
'''

x = 0
async def run_in_background_always():
    global x
    while True:
        print(x)
        x += 1
        await asyncio.sleep(0.5)

async def catches_the_global():
    data = []
    while len(data) < 2:
        data.append(x)
        await asyncio.sleep(1.1)
    return data   


async def main():
    task1 = asyncio.create_task(run_in_background_always())
    result = await catches_the_global()
    print(result)
    task1.cancel()
    

asyncio.run(main())

'''
0
1
2
3
4
[0, 3]
'''

