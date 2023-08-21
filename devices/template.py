import machine
import uasyncio as asyncio


class Device:

    running = False

    def reset(self):
        """Reset device."""
        pass
    
    async def run():
        """Async main routine."""
        self.running = True
        while self.running:
            await asyncio.sleep_ms(100)

    def handle(self, new_command, *args, **kwargs):
        """Handle new mqtt message."""
        pass


device_instance = Device()
