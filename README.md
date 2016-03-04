SLUT
====
SLack UTilities

*As an administrator I want to grab all the files uploaded by the users of my slack organization.*

slut is a simple script using the slack api, which allow you to grab all the files uploaded by user on
the slack of your organization. You only need to have administrator right on the slack to use it.

## How To

**slut** require python2.7 to run.

You'll need the following dependencies: *requests, argparse, subprocess, json, signal, wget, sys, os*.
Non standart are available with `pip`

As specified earlier, **slut** require to be administrator, morever you will need a slack token to call 
the API.

File download require connection and credential to the slack api. **slut** do not embed the connection to 
the API,however **slut** will use existing cookie. Just connect to your slack account on you browser
then export your cookies in a file, and specify the file with the **slut** command line.

You can specify any of these option through the commandline or just edit the script as they are only 
few global on the top of the file.

## Example usage

Here is a simple *slut* usage:

```Bash
> ./slut.py backup --token "SLACK-TOKEN" --cookies cookies.txt --output backup
```

## License

This is free and unencumbered software released into the public domain.
See details in the LICENSE file at the root of the repository.
