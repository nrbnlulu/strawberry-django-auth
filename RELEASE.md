Release type: patch

Fix bug in removal of JWT prefix.
In the current implementation if a token happens to contain any trailing J, W or T chars they are also removed.
This fix ensures we're only interested in the prefix as a substring.
