==================
Project Management
==================

Pull Request Code Review
------------------------

All code contributions are sent using a GitHub Pull Request, for example: https://github.com/hasadna/Open-Knesset/pull/556

When you start reviewing a pull request, assign it to yourself so that we won't have 2 people reviewing the same code together.

You should review both the code, but also the change itself, make sure it fits Open Knesset and our needs.

If in doubt, raise the issue on the forum or in slack.

Keep in mind that when dealing with volunteers, you should make sure they feel welcome to contribute more code.

Merging an approved pull request
--------------------------------

After a pull request is approved, you can merge it. Currently, this is done right after merging by the same person.

So, to merge, you just click the "Merge" button in the pull request (assuming you have write permissions).

Once it's merged to master, you should also update the release notes: https://github.com/hasadna/Open-Knesset/releases

If there is an existing "Draft" release - you can add it to that release.

If there is no "draft" release" - you can create a new release, just bump the relevant number in the version.

Look at a few previous releases to see what's written in the release notes, and how the versions are numbered.

Generally, release notes are meant for non technical people as well, so you should write a few words about the
changes that were introduced. Also, you can write deployment notes if any special actions should be performed
before or after the deployment.

Deploying a release
-------------------

Once you have some pull requests merged you might want to deploy the release. The release should be published before deployment (click "Publish" button in GitHub edit release page). This allows us to know which version was deployed. For technical details about how to deploy see the DevOps documentation.
