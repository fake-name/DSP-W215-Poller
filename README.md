DSP-W215 Power consumption monitor.
=======

An Open Source energy consumption monitoring tool for D-Link DSP-W215 "Smart" outlets.

This uses some of the undocumented features of the CGI interface provided by DSP-W215 outlets to periodically read power consumption information, and feed it into an emoncms instance.

All DSP-W215 related code is in `dspLog.py`. `EmonFeeder.py` is just the emoncms related facilities.

------

Note: While this does work, D-Link could very well break it at any time with a product update.
Really, Just buy Ubiquiti mPower monitor/control plugs. They actually have their API documented (unofficially, but by actual Ubnt employees): https://community.ubnt.com/t5/mFi/mPower-mFi-Switch-and-mFi-In-Wall-Outlet-HTTP-API/td-p/1076449

