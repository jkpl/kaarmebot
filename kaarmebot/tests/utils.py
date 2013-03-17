class Arguments(object):
    def __init__(self, args, kwargs):
        self.args = args
        self.kwargs = kwargs

    def __contains__(self, target):
        return (target in self.args or
                target in self.kwargs.values())

    def __getitem__(self, index):
        return self.args[index] or self.kwargs[index]


class ArgumentCaptor(object):
    def __init__(self):
        self.all_arguments = []
        self.last_arguments = None

    def capture(self, *args, **kwargs):
        arguments = Arguments(args, kwargs)
        self.last_arguments = arguments
        self.all_arguments.append(arguments)

    def __call__(self, *args, **kwargs):
        self.capture(*args, **kwargs)


class FakeProvider(ArgumentCaptor):
    def __init__(self, provided):
        super(FakeProvider, self).__init__()
        self.provided = provided

    def __call__(self, *args, **kwargs):
        super(FakeProvider, self).__call__(*args, **kwargs)
        return self.provided
