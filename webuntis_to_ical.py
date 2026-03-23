  File "/opt/hostedtoolcache/Python/3.12.13/x64/lib/python3.12/site-packages/webuntis/session.py", line 89, in login
    raise errors.BadCredentialsError('Missing config: ' + str(e))
webuntis.errors.BadCredentialsError: Missing config: 'No value for key: useragent'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/runner/work/stundenplan-ical/stundenplan-ical/webuntis_to_ical.py", line 139, in <module>
    main()
  File "/home/runner/work/stundenplan-ical/stundenplan-ical/webuntis_to_ical.py", line 99, in main
    with webuntis.Session(
         ^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.13/x64/lib/python3.12/site-packages/webuntis/session.py", line 40, in __exit__
    self.logout(suppress_errors=True)
  File "/opt/hostedtoolcache/Python/3.12.13/x64/lib/python3.12/site-packages/webuntis/session.py", line 60, in logout
    self._request('logout')
  File "/opt/hostedtoolcache/Python/3.12.13/x64/lib/python3.12/site-packages/webuntis/session.py", line 124, in _request
    data = rpc_request(self.config, method, params or {})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.13/x64/lib/python3.12/site-packages/webuntis/utils/remote.py", line 43, in rpc_request
    useragent = config['useragent']
                ~~~~~~^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.13/x64/lib/python3.12/site-packages/webuntis/utils/misc.py", line 87, in __getitem__
    raise KeyError('No value for key: ' + key)
KeyError: 'No value for key: useragent'
Error: Process completed with exit code 1.
