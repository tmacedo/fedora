Summary: redis
Name: redis
Version: 1.02
Release: 1
License: BSD
Group: Applications/Multimedia
URL: http://code.google.com/p/redis/

Source: http://redis.googlecode.com/files/redis-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

BuildRequires: gcc, make
Requires(post): /sbin/chkconfig /usr/sbin/useradd
Requires(preun): /sbin/chkconfig, /sbin/service
Requires(postun): /sbin/service
Provides: redis

Packager: Jason Priebe <jpriebe@cbcnewmedia.com>

%description
Redis is a key-value database. It is similar to memcached but the dataset is 
not volatile, and values can be strings, exactly like in memcached, but also 
lists and sets with atomic operations to push/pop elements.

In order to be very fast but at the same time persistent the whole dataset is 
taken in memory and from time to time and/or when a number of changes to the 
dataset are performed it is written asynchronously on disk. You may lose the
last few queries that is acceptable in many applications but it is as fast 
as an in memory DB (beta 6 of Redis includes initial support for master-slave 
replication in order to solve this problem by redundancy).

Compression and other interesting features are a work in progress. Redis is 
written in ANSI C and works in most POSIX systems like Linux, *BSD, Mac OS X, 
and so on. Redis is free software released under the very liberal BSD license. 


%prep
%setup

%{__cat} <<EOF >redis.sysconfig
# Redis configuration file example

# By default Redis does not run as a daemon. Use 'yes' if you need it.
# Note that Redis will write a pid file in /var/run/redis.pid when daemonized.
daemonize yes

# When run as a daemon, Redis write a pid file in /var/run/redis.pid by default.
# You can specify a custom pid file location here.
pidfile /var/run/redis/redis.pid

# Accept connections on the specified port, default is 6379
port 6379

# If you want you can bind a single interface, if the bind option is not
# specified all the interfaces will listen for connections.
#
# bind 127.0.0.1

# Close the connection after a client is idle for N seconds (0 to disable)
timeout 300

# Save the DB on disk:
#
#   save <seconds> <changes>
#
#   Will save the DB if both the given number of seconds and the given
#   number of write operations against the DB occurred.
#
#   In the example below the behaviour will be to save:
#   after 900 sec (15 min) if at least 1 key changed
#   after 300 sec (5 min) if at least 10 keys changed
#   after 60 sec if at least 10000 keys changed
save 900 1
save 300 10
save 60 10000

# For default save/load DB in/from the working directory
# Note that you must specify a directory not a file name.
dir %{_localstatedir}/lib/redis

# Set server verbosity to 'debug'
# it can be one of:
# debug (a lot of information, useful for development/testing)
# notice (moderately verbose, what you want in production probably)
# warning (only very important / critical messages are logged)
loglevel notice

# Specify the log file name. Also 'stdout' can be used to force
# the demon to log on the standard output. Note that if you use standard
# output for logging but daemonize, logs will be sent to /dev/null
logfile %{_localstatedir}/log/redis/redis.log

# Set the number of databases.
databases 16

################################# REPLICATION #################################

# Master-Slave replication. Use slaveof to make a Redis instance a copy of
# another Redis server. Note that the configuration is local to the slave
# so for example it is possible to configure the slave to save the DB with a
# different interval, or to listen to another port, and so on.

# slaveof <masterip> <masterport>

################################## SECURITY ###################################

# Require clients to issue AUTH <PASSWORD> before processing any other
# commands.  This might be useful in environments in which you do not trust
# others with access to the host running redis-server.
#
# This should stay commented out for backward compatibility and because most
# people do not need auth (e.g. they run their own servers).

# requirepass foobared

################################### LIMITS ####################################

# Set the max number of connected clients at the same time. By default there
# is no limit, and it's up to the number of file descriptors the Redis process
# is able to open. The special value '0' means no limts.
# Once the limit is reached Redis will close all the new connections sending
# an error 'max number of clients reached'.

# maxclients 128

############################### ADVANCED CONFIG ###############################

# Glue small output buffers together in order to send small replies in a
# single TCP packet. Uses a bit more CPU but most of the times it is a win
# in terms of number of queries per second. Use 'yes' if unsure.
glueoutputbuf yes

# Use object sharing. Can save a lot of memory if you have many common
# string in your dataset, but performs lookups against the shared objects
# pool so it uses more CPU and can be a bit slower. Usually it's a good
# idea.
shareobjects no
EOF

%{__cat} <<EOF >redis.logrotate
%{_localstatedir}/log/redis/*log {
    missingok
}
EOF

%{__cat} <<'EOF' >redis.sysv
#!/bin/bash
#
# Init file for redis
#
# Written by Jason Priebe <jpriebe@cbcnewmedia.com>
#
# chkconfig: - 80 12
# description: A persistent key-value database with network interface
# processname: redis-server
# config: /etc/redis.conf
# pidfile: /var/run/redis/redis.conf

source %{_sysconfdir}/rc.d/init.d/functions

RETVAL=0
prog="redis-server"

start() {
	echo -n $"Starting $prog: "
	daemon --user redis --pidfile %{_localstatedir}/run/redis/redis.pid %{_sbindir}/$prog /etc/redis.conf
	RETVAL=$?
	echo
	[ $RETVAL -eq 0 ] && touch %{_localstatedir}/lock/subsys/$prog
	return $RETVAL
}

stop() {
    PID=`cat /var/run/redis/redis.pid 2>/dev/null`
    if [ -n "$PID" ]; then
        echo "Shutdown may take a while; redis needs to save the entire database";
        echo -n $"Shutting down $prog: "
        /usr/bin/redis-cli shutdown
        if checkpid $PID 2>&1; then
            echo_failure
            RETVAL=1
        else
            rm -f /var/lib/redis/temp*rdb
            rm -f /var/lock/subsys/$prog
            echo_success
            RETVAL=0
        fi
    else
        echo -n $"$prog is not running"
        echo_failure
        RETVAL=1
    fi

    echo
    return $RETVAL
}

restart() {
	stop
	start
}

condrestart() {
    [-e /var/lock/subsys/$prog] && restart || :
}

case "$1" in
  start)
	start
	;;
  stop)
	stop
	;;
  status)
	status -p /var/run/redis/redis.pid $prog
	RETVAL=$?
	;;
  restart)
	restart
	;;
  condrestart|try-restart)
	condrestart
	;;
   *)
	echo $"Usage: $0 {start|stop|status|restart|condrestart}"
	RETVAL=1
esac

exit $RETVAL
EOF


%build
%{__make}

%install
%{__rm} -rf %{buildroot}
mkdir -p %{buildroot}%{_bindir}
%{__install} -Dp -m0755 redis-server %{buildroot}%{_sbindir}/redis-server
%{__install} -Dp -m0755 redis-benchmark %{buildroot}%{_bindir}/redis-benchmark
%{__install} -Dp -m0755 redis-cli %{buildroot}%{_bindir}/redis-cli

%{__install} -Dp -m0755 redis.logrotate %{buildroot}%{_sysconfdir}/logrotate.d/redis
%{__install} -Dp -m0755 redis.sysv %{buildroot}%{_sysconfdir}/rc.d/init.d/redis
%{__install} -Dp -m0644 redis.sysconfig %{buildroot}%{_sysconfdir}/redis.conf
mkdir -p %{buildroot}%{_localstatedir}/lib/redis
mkdir -p %{buildroot}%{_localstatedir}/log/redis
mkdir -p %{buildroot}%{_localstatedir}/run/redis

%pre
/usr/sbin/useradd -c 'Redis' -u 499 -s /sbin/nologin -r -d %{_localstatedir}/lib/redis redis 2> /dev/null || :

%preun
if [ $1 = 0 ]; then
    # make sure redis service is not running before uninstalling

    # when the preun section is run, we've got stdin attached.  If we
    # call stop() in the redis init script, it will pass stdin along to
    # the redis-cli script; this will cause redis-cli to read an extraneous
    # argument, and the redis-cli shutdown will fail due to the wrong number
    # of arguments.  So we do this little bit of magic to reconnect stdin
    # to the terminal
    term="/dev/$(ps -p$$ --no-heading | awk '{print $2}')"
    exec < $term

    /sbin/service redis stop > /dev/null 2>&1 || :
    /sbin/chkconfig --del redis
fi

%post
/sbin/chkconfig --add redis

%clean
%{__rm} -rf %{buildroot}

%files
%defattr(-, root, root, 0755)
%doc doc/*.html
%{_sbindir}/redis-server
%{_bindir}/redis-benchmark
%{_bindir}/redis-cli
%{_sysconfdir}/rc.d/init.d/redis
%config(noreplace) %{_sysconfdir}/redis.conf
%{_sysconfdir}/logrotate.d/redis
%dir %attr(0770,redis,redis) %{_localstatedir}/lib/redis
%dir %attr(0755,redis,redis) %{_localstatedir}/log/redis
%dir %attr(0755,redis,redis) %{_localstatedir}/run/redis

%changelog
* Fri Sep 11 2009 - jpriebe at cbcnewmedia dot com 1.0-1
- redis updated to version 1.0 stable

* Mon Jun 01 2009 - jpriebe at cbcnewmedia dot com 0.100-1
- Massive redis changes in moving from 0.09x to 0.100
- removed log timestamp patch; this feature is now part of standard release

* Tue May 12 2009 - jpriebe at cbcnewmedia dot com 0.096-1
- A memory leak when passing more than 16 arguments to a command (including
  itself). 
- A memory leak when loading compressed objects from disk is now fixed. 

* Mon May 04 2009 - jpriebe at cbcnewmedia dot com 0.094-2
- Patch: applied patch to add timestamp to the log messages
- moved redis-server to /usr/sbin
- set %config(noreplace) on redis.conf to prevent config file overwrites
  on upgrade

* Fri May 01 2009 - jpriebe at cbcnewmedia dot com 0.094-1
- Bugfix: 32bit integer overflow bug; there was a problem with datasets 
  consisting of more than 20,000,000 keys resulting in a lot of CPU usage 
  for iterated hash table resizing.

* Wed Apr 29 2009 - jpriebe at cbcnewmedia dot com 0.093-2
- added message to init.d script to warn user that shutdown may take a while

* Wed Apr 29 2009 - jpriebe at cbcnewmedia dot com 0.093-1
- version 0.093: fixed bug in save that would cause a crash
- version 0.092: fix for bug in RANDOMKEY command

* Fri Apr 24 2009 - jpriebe at cbcnewmedia dot com 0.091-3
- change permissions on /var/log/redis and /var/run/redis to 755; this allows
  non-root users to check the service status and to read the logs

* Wed Apr 22 2009 - jpriebe at cbcnewmedia dot com 0.091-2
- cleanup of temp*rdb files in /var/lib/redis after shutdown
- better handling of pid file, especially with status

* Tue Apr 14 2009 - jpriebe at cbcnewmedia dot com 0.091-1
- Initial release.

