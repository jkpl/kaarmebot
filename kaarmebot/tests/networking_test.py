import unittest
import mockito as m
import kaarmebot.networking as n


class TestSimpleSocketGreenlet(unittest.TestCase):
    example_string = "this is an example string"

    def setUp(self):
        self.sock_mock = m.mock()
        self.file_mock = m.mock()

        m.when(n.s).socket(m.any(), m.any()).thenReturn(self.sock_mock)
        m.when(self.sock_mock).makefile().thenReturn(self.file_mock)
        self.set_sock_mock_receive_string(self.example_string)

        self.address = 'some_address'
        self.client = n.SimpleSocketGreenlet(
            self.address, self.message_callback, self.close_callback)

        self.lines = []
        self.close_called = False

    def tearDown(self):
        m.unstub()

    def set_sock_mock_receive_string(self, string):
        m.when(self.file_mock).readline().thenReturn(
            string).thenRaise(IOError('Expected error'))

    def message_callback(self, line):
        self.lines.append(line)

    def close_callback(self):
        self.close_called = True

    def test_socket_close_and_close_handlers_are_called_on_close(self):
        self.client.running = True
        self.client.close()

        m.verify(self.sock_mock).close()
        self.assertTrue(self.close_called)

    def test_socket_connect_and_close_is_called_on_run(self):
        self.client.start()
        self.client.join()

        m.verify(self.sock_mock).connect(self.address)

    def test_socket_sendall_is_called_on_send(self):
        self.client.send(self.example_string)

        m.verify(self.sock_mock).sendall(self.example_string + '\r\n')

    def test_callback_gets_one_line_from_socket(self):
        self.client.start()
        self.client.join()

        self.assertItemsEqual(self.lines, [self.example_string])
