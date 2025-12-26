"""Integration tests for WebSocket streaming functionality."""
import os
import time
import unittest
import asyncio
import json

import requests
import websockets


@unittest.skipUnless(os.getenv('RUN_INTEGRATION_TESTS'), 'Integration tests disabled')
class TestWebSocketIntegration(unittest.TestCase):
    """Integration tests for WebSocket real-time streaming."""

    def setUp(self):
        """Set up test client and create a test character/session."""
        self.base_url = "http://backend:8000"
        self.ws_url = "ws://backend:8000"
        self.timeout = 10

        # Start game session (skips separate character creation)
        game_response = requests.post(
            f'{self.base_url}/game/start',
            json={'name': 'WebSocketTester', 'character_class': 'wizard'},
            timeout=self.timeout
        )
        self.assertEqual(game_response.status_code, 200)
        game_data = game_response.json()
        self.game_id = game_data['game_id']

    async def async_websocket_connection_test(self):
        """Test WebSocket connection is established and sends connected message."""
        async with websockets.connect(
            f'{self.ws_url}/ws/game/{self.game_id}'
        ) as websocket:
            # Receive connected message
            data_str = await websocket.recv()
            data = json.loads(data_str)

            self.assertEqual(data['type'], 'connected')
            self.assertEqual(data['game_id'], self.game_id)
            self.assertIn('session', data)

    def test_websocket_connection_established(self):
        """Test WebSocket connection is established and sends connected message."""
        asyncio.run(self.async_websocket_connection_test())

    async def async_command_streaming_test(self):
        """Test command execution streams response word-by-word."""
        async with websockets.connect(
            f'{self.ws_url}/ws/game/{self.game_id}'
        ) as websocket:
            # Receive and ignore connected message
            await websocket.recv()

            # Send command
            await websocket.send(json.dumps({
                'command': 'look around',
                'parameters': None
            }))

            # Should receive typing indicator first
            typing_str = await websocket.recv()
            typing_msg = json.loads(typing_str)
            self.assertEqual(typing_msg['type'], 'typing')
            self.assertIn('agent', typing_msg)

            # Collect streaming chunks
            chunks = []
            while True:
                msg_str = await websocket.recv()
                msg = json.loads(msg_str)
                if msg['type'] == 'chunk':
                    chunks.append(msg['data'])
                elif msg['type'] == 'complete':
                    break

            # Verify we received multiple chunks (streaming happened)
            self.assertGreater(len(chunks), 10, "Should receive multiple word chunks")

            # Verify chunks reconstruct a coherent response
            full_response = ''.join(chunks)
            self.assertGreater(len(full_response), 50)
            self.assertIn('cave', full_response.lower())

    def test_websocket_command_streaming(self):
        """Test command execution streams response word-by-word."""
        asyncio.run(self.async_command_streaming_test())

    async def async_complete_message_test(self):
        """Test complete message contains all expected fields."""
        async with websockets.connect(
            f'{self.ws_url}/ws/game/{self.game_id}'
        ) as websocket:
            await websocket.recv()  # connected

            await websocket.send(json.dumps({
                'command': 'look',
                'parameters': None
            }))

            # Skip to complete message
            msg_str = await websocket.recv()
            msg = json.loads(msg_str)
            while msg['type'] != 'complete':
                msg_str = await websocket.recv()
                msg = json.loads(msg_str)

            # Verify complete message structure
            self.assertEqual(msg['type'], 'complete')
            self.assertIn('game_id', msg)
            self.assertIn('turn', msg)
            self.assertIn('agent', msg)
            self.assertIn('success', msg)
            self.assertIn('session', msg)

            # Verify session was updated
            self.assertEqual(msg['session']['turn_count'], 1)

    def test_websocket_complete_message_format(self):
        """Test complete message contains all expected fields."""
        asyncio.run(self.async_complete_message_test())

    async def async_error_handling_test(self):
        """Test WebSocket sends error message for invalid commands."""
        async with websockets.connect(
            f'{self.ws_url}/ws/game/{self.game_id}'
        ) as websocket:
            await websocket.recv()  # connected

            # Send invalid JSON
            await websocket.send("invalid json")

            # Should receive error message
            error_str = await websocket.recv()
            error_msg = json.loads(error_str)
            self.assertEqual(error_msg['type'], 'error')
            self.assertIn('message', error_msg)

    def test_websocket_error_handling(self):
        """Test WebSocket sends error message for invalid commands."""
        asyncio.run(self.async_error_handling_test())

    async def async_multiple_commands_test(self):
        """Test multiple commands can be sent sequentially."""
        async with websockets.connect(
            f'{self.ws_url}/ws/game/{self.game_id}'
        ) as websocket:
            await websocket.recv()  # connected

            commands = ['look around', 'examine rope']

            for cmd in commands:
                await websocket.send(json.dumps({
                    'command': cmd,
                    'parameters': None
                }))

                # Wait for complete message
                msg_str = await websocket.recv()
                msg = json.loads(msg_str)
                while msg['type'] != 'complete':
                    msg_str = await websocket.recv()
                    msg = json.loads(msg_str)

                self.assertEqual(msg['type'], 'complete')
                self.assertTrue(msg['success'])

    def test_websocket_multiple_commands_sequential(self):
        """Test multiple commands can be sent sequentially."""
        asyncio.run(self.async_multiple_commands_test())

    async def async_session_state_test(self):
        """Test session state is updated and returned in complete message."""
        async with websockets.connect(
            f'{self.ws_url}/ws/game/{self.game_id}'
        ) as websocket:
            connected_str = await websocket.recv()
            connected = json.loads(connected_str)
            initial_turn = connected['session']['turn_count']

            # Execute command
            await websocket.send(json.dumps({
                'command': 'look',
                'parameters': None
            }))

            # Get complete message
            msg_str = await websocket.recv()
            msg = json.loads(msg_str)
            while msg['type'] != 'complete':
                msg_str = await websocket.recv()
                msg = json.loads(msg_str)

            # Verify turn count incremented
            self.assertEqual(msg['session']['turn_count'], initial_turn + 1)

    def test_websocket_session_state_updates(self):
        """Test session state is updated and returned in complete message."""
        asyncio.run(self.async_session_state_test())

    async def async_chunk_timing_test(self):
        """Test chunks are delivered with appropriate delays."""
        async with websockets.connect(
            f'{self.ws_url}/ws/game/{self.game_id}'
        ) as websocket:
            await websocket.recv()  # connected

            await websocket.send(json.dumps({
                'command': 'look',
                'parameters': None
            }))

            await websocket.recv()  # typing

            # Measure time to receive first few chunks
            start = time.time()
            chunk_times = []
            for _ in range(5):
                msg_str = await websocket.recv()
                msg = json.loads(msg_str)
                if msg['type'] == 'chunk':
                    chunk_times.append(time.time() - start)

            # Verify chunks arrive with delays (not all at once)
            # With 80ms delay, 5 chunks should take ~320ms minimum
            if len(chunk_times) >= 2:
                total_time = chunk_times[-1] - chunk_times[0]
                self.assertGreater(total_time, 0.2, "Chunks should have delays")

    def test_websocket_chunk_timing(self):
        """Test chunks are delivered with appropriate delays."""
        asyncio.run(self.async_chunk_timing_test())


if __name__ == '__main__':
    unittest.main()
