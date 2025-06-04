import asyncio


#  wait for elements to start the app without errors
async def wait_for_elements(locator, count, timeout=10000, poll_interval=200):
    # Wait until locator finds at least `count` elements
    elapsed = 0

    while elapsed < timeout:
        elements_found = await locator.count()
        if elements_found >= count:
            print("✅ waited successfully for element")
            return True
        await asyncio.sleep(poll_interval / 1000)
        elapsed += poll_interval

    # Raise error if not enough elements found in time
    raise TimeoutError(f"Expected at least {count} elements, but found {elements_found} after {timeout}ms.")

