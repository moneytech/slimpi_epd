#!/usr/bin/env ipython
#!/usr/bin/env python
# coding: utf-8


# In[125]:


#get_ipython().run_line_magic('alias', 'nbconvert nbconvert ./Configuration.ipynb')

#get_ipython().run_line_magic('nbconvert', '')




# In[1]:


import sys
import argparse
import configparser
import re
from pathlib import Path

import logging




# In[2]:


logging.basicConfig(level=logging.DEBUG, format='%(name)s:%(funcName)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)




# In[3]:


# class file():
#     '''class that creates a pathlib.Path().expanduser().resolve() object from a string
#     Args:
#         file(`str`): string representation of a file path'''
#     def __init__(self, file):
#         self.file = file
        
#     @property
#     def file(self):
#         return self._file
    
#     @file.setter
#     def file(self, file):
#         if file:
#             f = Path(file).expanduser().resolve()
#             if f.exists():
#                 self._file = f
#                 self.parent = f.parent
#                 self.exists = True
#             else:
#                 logging.warning(f'file does not exist: {f}')
#                 self._file = None
#                 self.parent = None
#                 self.exists = False
#         else:
#             self._file = None
#             self.exists = False
            
#     def __repr__(self) -> Path:
#         return repr(str(self.file))
    
#     def __str__(self):
#         return(str(self.file))




# In[68]:


def merge_dict(a, b):
    '''recursivley merge two dictionarys overwriting values
        known issue: if `a` contains a different data type than `b`, `b`
        will completely overwrite the data in `a`
        
    Args:
        a(`dict`): nested dictionary
        b(`dict`): nested dictionary 
        
    Returns:
        dict
    '''
    c = dict(a) # make a copy of dict `a`
    for key in b:
        if key in a:
            if isinstance(b[key], dict) and isinstance(a[key], dict):
                c[key] = merge_dict(a[key], b[key])
            else:
                c[key] = b[key]
        else:
            c[key] = b[key]
    return c
            
            




# In[4]:


def fullPath(path):
    return Path(path).expanduser().resolve()




# In[149]:


class Options():
    '''command line parser object 
    
    Args:
        args(`list`): sys.argv is typically passed here
        
    Properties:
        parser(`argparse.ArgumentParser`): argument parser object
        args(`list`): list of arguments
        options(NameSpace): argument parser generated namespace of arguments
        opts_dict(`dict`): namespace -> dictionary'''
    def __init__(self, args=None):
        self.parser = argparse.ArgumentParser()
        self.args = args
        self.options = None
        self.opts_dict = None
        self.nested_opts_dict = None
    
#     @property
#     def parser(self):
#         '''The argparser object'''
#         return self._parser
    
#     @parser.setter
#     def parser(self, parser):
#         if parser:
#             self._parser = parser
    
    @property
    def options(self):
        '''argparser namespace of the parsed arguments'''
        return self._options
        
    
    @options.setter
    def options(self, options):
        if options:
            self._options = options
        else:
            self._options = None
    
    def parse_args(self, args=None, discard_false=[], discard_none=[]):
        '''parse arguments and set dictionaries
        
        Args:
            args(`list`): list of commandline arguments to process
            set_args(`bool`): set arguments property (default=True)
            discard_false(`list`): discard any keys that are set as False
            discard_none(`list`): discard any keys that are set as None
            
        Sets:
            args(`list`): list of arguments
            options(Nampespace): namespace of parsed known arguments'''
            
        if args:
            my_args = args
        else:
            my_args = self.args
                
        if my_args:
            options, unknown = self.parser.parse_known_args()
            logging.warning(f'ignoring unknown options: {unknown}')
            self.options = options
            self.opts_dict = options
            for key in discard_false:
                try:
                    if self.opts_dict[key] is False:
                        logging.info(f'popping: {key}')
                        self.opts_dict.pop(key)
                except KeyError as e:
                    logging.debug(f'{key} not found, ignoring')
                    
            for key in discard_none:
                try:
                    if self.opts_dict[key] is None:
                        logging.info(f'popping: {key}')
                        self.opts_dict.pop(key)                    
                except KeyError as e:
                    logging.debug(f'{key} not found, ignoring')
                    
            self.nested_opts_dict = self.opts_dict
 
    
    @property
    def opts_dict(self):
        '''dictionary of namespace of parsed options
        
        Args:
            options(namespace): configparser.ConfigParser.parser.parse_known_args() options
        
        Returns:
            `dict` of `namespace` of parsed options
            '''
        return self._opts_dict
    
    @opts_dict.setter
    def opts_dict(self, options):
        if options:
            self._opts_dict = vars(self.options)
        else:
            self._opts_dict = None

    @property
    def nested_opts_dict(self):
        '''nested dictionary of configuration options
            `nested_opts_dict` format follows the same format as ConfigFile.config_dict
            see add_argument for more information 
            
        Args:
            opts_dict(`dict`): flat dictionary representation of parser arguments'''
        return self._nested_opts_dict
    
    @nested_opts_dict.setter
    def nested_opts_dict(self, opts_dict):
        if opts_dict:
            # nest everything that comes from the commandline under this key
            cmd_line = '__cmd_line'
            d = {}
            # create the key for command line options
            d[cmd_line] = {}

            # process all the keys
            for key in opts_dict:
                # match those that are in the format [[SectionName]]__[[OptionName]]
                match = re.match('^(\w+)__(\w+)$', key)
                if match:
                    section = match.group(1)
                    option = match.group(2)
                    if not section in d:
                        d[section] = {}
                    d[section][option] = opts_dict[key]
                else:
                    d[cmd_line][key] = opts_dict[key]
            self._nested_opts_dict = d
        else:
            self._nested_opts_dict = None

    
#     def _parse_args(self):
#         '''parse known arguments and discard unknown arguments'''
#         options, unknown = self.parser.parse_known_args()
#         logging.info(f'discarding unknown commandline arguments: {unknown}')
#         self.options = options
    
    def add_argument(self, *args, **kwargs):
        '''add arguments to the parser.argparse.ArgumentParser object 
            use the standard *args and **kwargs for argparse
            
            arguments added using the kwarg `dest=section__option_name`
            note the format [[section_name]]__[[option_name]]
            will be nested in the `opts_dict` property in the format:
            {'section': 
                        {'option_name': 'value'
                         'option_two': 'value'}}
                         
            the `nested_opts_dict` property can then be merged with a ConfigFile 
            `config_dict` property using the merge_dicts() function:
            merge_dicts(obj:`ConfigFile.config_dict`, obj:`Options.nested_opts_dict`) 
            to override the options set in the configuration file(s) with
            commandline arguments
        
        Args:
            *args, **kwargs'''
        try:
            self.parser.add_argument(*args, **kwargs)
        except argparse.ArgumentError as e:
            logging.warning(f'failed adding conflicting option {e}')




# In[150]:


# o = Options(sys.argv)

# o.add_argument('-c', '--config-file', type=str, default=None, 
#                         help='use the specified configuration file. Default is stored in ~/.config/myApp/config.ini')
# o.add_argument('-l', '--log-level', type=str, dest='logging__log_level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
#                         default = None,
#                         help='set logging level: DEBUG, INFO, WARNING, ERROR')


# o.parse_args(discard_none=['logging__log_level', 'foo'])
# print(o.opts_dict)
# print(o.nested_opts_dict)




# In[127]:


class ConfigFile():
    def __init__(self, default=None, user=None):
        self.cfg_files = []
#         self.default = file(default)
        self.default = fullPath(default)
#         self.user = file(user)
        self.user = fullPath(user)
        self.parse_config()
        
    def parse_config(self):
        '''parse the config file(s) overriding the default configuration 
            with the user configuration (if provided)
            
        Sets:
            config(obj:`configparser.ConfigParser`): parser object
            config_dict(`dict` of `dict` of `str`): dictionary representation of 
                merged configuration files'''
        if self.default.exists:
#             self.cfg_files.append(self.default.file)
            self.cfg_files.append(self.default)
        if self.user.exists:
#             self.cfg_files.append(self.user.file)
            self.cfg_files.append(self.user)
        if self.cfg_files:
            self.config = configparser.ConfigParser()
            self.config.read(self.cfg_files)
        
        if self.config.sections():
            self.config_dict = self._config_2dict(self.config)
        
        
    def _config_2dict(self, configuration):
        '''convert an argparse object into a dictionary

        Args:
            configuration(`configparser.ConfigParser`)

        Returns:
            `dict`'''
        d = {}
        for section in configuration.sections():
            d[section] = {}
            for opt in configuration.options(section):
                d[section][opt] = configuration.get(section, opt)

        return d    




# In[64]:


# c = ConfigFile(default='./slimpi.cfg', user='~/.config/com.txoof.slimpi/slimpi.cfg')

# c.cfg_files

# c.config.options('main')

# c.config_dict



# create a "Default" configuration object from the builtin config
# Create a "user" configuration based on the user config
# merge the default and the user overriding the default with the user version
# merge the command line over the top of everything
# 
# finally creating a dictionary of options


# In[69]:


# merge_dict(c.config_dict, o.nested_opts_dict)




# In[23]:


# aa = dict(a)
# bb = dict(b)

# aa = {'a': {'cow': 'cynthia', 'bear': 'barney', 'horse': 'ed'}, 'b': 10, 'c': [1, 3, 5, 7, 9], 'foo': 'bar'}
# bb = {'a': {'cow': 'Zed', 'bear': 'barney', 'zebra': 'yellow'}, 'b': 10, 'c': [2, 4, 6, 8, 10]}

# print(aa)

# print(bb)

# merge_dict(aa, bb)




# In[ ]:





