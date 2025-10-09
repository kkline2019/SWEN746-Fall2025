# Repo Miner

Stub README for the Repo Miner project.

---

To KKLine:

It seems that the CI pipeline was just delayed. We already fixed the pipeline during office hours.
If you want a push to trigger the CI (not just a push to the main branch), you need to change
```
push:
  branches: main
```
to
```
push:
  branches: [ "**" ]
```
Additionally, to avoid losing points, please ensure the status check passes instead of failing.

Please delete the notes above 👆🏻 before you submit your assignment.
