# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import argparse
import copy

# (instead of subclassing argparse._SubParsersAction, we monkey-patch it,
#  because argcomplete has special-cases for the _SubParsersAction class that
#  it's impossible to extend to another class)
#
# add a add_parser_async function, which allows a subparser to be added whose
# options are not evaluated until the subparser has been selected. This allows
# us to defer loading the modules for all the subcommands until they are
# actually:
def _SubParsersAction_addParserAsync(self, name, *args, **kwargs):
    if not 'callback' in kwargs:
        raise ValueError('callback=fn(parser) argument must be specified')
    callback = kwargs['callback']
    del kwargs['callback']
    parser = self.add_parser(name, *args, **kwargs)
    parser._lazy_load_callback = callback
    return None
argparse._SubParsersAction.add_parser_async = _SubParsersAction_addParserAsync

def _wrapSubParserActionCall(orig_call):
    def wrapped_call(self, parser, namespace, values, option_string=None):
        parser_name = values[0]
        if parser_name in self._name_parser_map:
            subparser = self._name_parser_map[parser_name]
            if hasattr(subparser, '_lazy_load_callback'):
                # the callback is responsible for adding the subparser's own
                # arguments:
                subparser._lazy_load_callback(subparser)
        # now we can go ahead and call the subparser action: its arguments are
        # now all set up
        original_values = copy.copy(vars(namespace))
        ret = orig_call(self, parser, namespace, values, option_string)
        # replace any argument value that was clobbered by a "None" value with
        # its value from the root parser. (the subparser re-sets the default
        # values for options with are re-used between the root and sub-parsers)
        for k, v in original_values.items():
            if v is not None and hasattr(namespace, k):
                if getattr(namespace, k) is None:
                    setattr(namespace, k, v)
        return ret
    return wrapped_call
argparse._SubParsersAction.__call__ = _wrapSubParserActionCall(argparse._SubParsersAction.__call__)

# we don't actually modify the parser itself (actually its impossible to do the
# above modifications by subclassing :()
ArgumentParser = argparse.ArgumentParser

