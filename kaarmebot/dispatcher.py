import collections


Message = collections.namedtuple('Message', ['source', 'target', 'contents'])


class MessageDispatcher:
    def __init__(self):
        self.routing_classes = {}

    def add_binding(self, routing_class, predicate, handler):
        rc = self.routing_classes.get(routing_class)
        if rc:
            rc.append((predicate, handler))
        else:
            self.routing_classes[routing_class] = [(predicate, handler)]

    def remove_binding(self, routing_class, predicate, handler):
        rc = self.routing_classes.get(routing_class)
        if rc:
            rc.remove((predicate, handler))

    def get_handlers_for_message(self, message):
        rc = self.routing_classes.get(message.__class__)
        if rc:
            for predicate, handler in rc:
                if predicate(message):
                    yield handler

    def dispatch(self, message):
        handler_generator = self.get_handlers_for_message(message)
        return [handler(message) for handler in handler_generator]
