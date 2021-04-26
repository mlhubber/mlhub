# A Test Suite for MLHub Utilising Exactly

Exactly comes from https://github.com/emilkarlen/exactly

Considered the older BATS but Exactly is being actively maintained and
seems to be comprehensive.

Install:

```
$ pip3 install exactly
```

20210426 Version 0.15.0

Create individual unit test cases in separate files within this
directory with *.case* filename extensions.

Begin file names with three digit numbers to imply an ordering. The
tests will be undertaken in that order as controlled by
`exactly.suite`.

Run the test suite from the parent directory:

```
$ exactly suite tests
```

Run individual tests within this directory:

```
$ exactly 200_fresh_install_pytempl.case
```

To show the actual output instead of running *assert* section:

```
$ exactly 200_fresh_install_pytempl.case --act
```

