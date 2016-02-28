========================
Feature toggles
========================

Sometimes we would like Develop new features but not expose them yet to users.
Perhaps we need to expose them only to Qa, or by user role (such as admins).

Maybe we need some backend model to start gathering data and calculations from real production data but not expose
this data in the view, while retaining the possibilty

Another use case can be rolling and exposing a feature only to a small sample of our users. We would like
to get input from real usage pattens before we proceed with rolling a feature to all users..

For all those use cases we can use feature flags/feature toggle.

A feature toggle can toggled on or off, globally or sometimes according to a specific condition.

You can (and should) read more about the `feature toggle pattern in Martin Fowler's blog`_

.. _feature toggle pattern in Martin Fowler's blog: http://martinfowler.com/articles/feature-toggles.html

Using "waffle" - a feature toggle framework for django
======================================================
We are currently using Django-Waffle as a feature toggle framework.
It allows using switches and flags (switches that accept the request and allow
configuring the on/off flag according to the user, request, environ and more)
You can use flags, switches and other *waffle* goodies in templates, views, javascript etc.
You can read more about operating waffle in `Waffle docs`_

.. _Waffle docs: http://waffle.readthedocs.org/en/v0.11/index.html


Note that when you add a feature toggle in the code without adding in the db (through admin or command) then
 The feature toggle is considered closed

Cleaning up after
=================

A common problem with feature toggles is forgetting to remove them when finished. after some time passes nobody
remembers anymore the original purpose of the toggle and no ones dare removing it. Even worst `things can happen`_
Please remove feature toggles when not needed any more.

 .. _things can happen: http://dougseven.com/2014/04/17/knightmare-a-devops-cautionary-tale/

