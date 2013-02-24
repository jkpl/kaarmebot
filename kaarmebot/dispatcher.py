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

    def add_bindings(self, *bindings):
        for binding in bindings:
            self.add_binding(*binding)

    def remove_binding(self, routing_class, predicate, handler):
        rc = self.routing_classes.get(routing_class)
        if rc:
            rc.remove((predicate, handler))

    def dispatch(self, message):
        rc = self.routing_classes.get(message.__class__)
        if rc:
            return self._generate_handler_results(rc, message)
        return []

    def _generate_handler_results(self, predicate_handler_pairs, message):
        results = []
        for predicate, handler in predicate_handler_pairs:
            match, result = get_predicate_handler_result_for_message(
                predicate, handler, message)
            if match:
                results.append(result)
        return results


def get_predicate_handler_result_for_message(predicate, handler, message):
    result = predicate(message)
    if result:
        return True, handler(message)
    return False, None
