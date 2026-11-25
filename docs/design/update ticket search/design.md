1)
Current update ticket status flow:
```bash
Simple Project
1) View active ticket
2) Create ticket
3) Update ticket status
4) Search tickets
5) Search code
6) Recently updated tickets
0) Exit
$ 3
Ticket ID: 
$ 3
```
Note: Remove this menu option completely

2)
Current search tickets flow:
```bash
Simple Project
1) View active ticket
2) Create ticket
3) Update ticket status
4) Search tickets
5) Search code
6) Recently updated tickets
0) Exit
$ 4
Search text or tag: test
#1 [fix] [active] test ticket (test) 2026-09-15
```
Note: Update this menu option.

Update it like this:
```bash
Simple Project
1) View active ticket
2) Create ticket
3) Search tickets (by text)
4) Search tickets (by tag)
5) Search code
6) Recently updated tickets
0) Exit
$ 3

Select search mode
1) Search active/open tickets
2) Search closed/cancelled tickets
0) Back to main menu
$ 1

Search text: 
$ test

Results:
1) [fix] [active] test ticket (test) 2026-09-15 Score: 3
2) [fix] [open] test ticket (test) 2026-09-14 Score: 2
3) [fix] [open] test ticket (test) 2026-09-10 Score: 1
Select a ticket to edit or return to main menu
$ 2

Edit ticket: # User is prompted to update each field one at a time
Title ('test ticket'): # Existing title is displayed and user can tweak it or hit enter to keep it
$ 
Description ('this is a test ticket'): # Existing description is displayed and user can tweak it or hit enter to keep it
$ 
Type ('fix'): # Validate that the type the user entered is valid
$ 
Status ('active'): # Validate that the status the user entered is valid
$ 
Tags ('test'): # comma seperated
$ 
Select an option:
1) Return to search results
2) Return to main menu
$ 2
```

3)
Current recently updated tickets flow:
```bash
Simple Project
1) View active ticket
2) Create ticket
3) Update ticket status
4) Search tickets
5) Search code
6) Recently updated tickets
0) Exit
$ 6

Results:
1) [fix] [active] test ticket (test) 2026-09-15
2) [fix] [open] test ticket (test) 2026-09-14
3) [fix] [open] test ticket (test) 2026-09-10
Select a ticket to edit or return to main menu
$ 2

Edit ticket: # User is prompted to update each field one at a time
Title ('test ticket'): # Existing title is automatically filled in here, user can just tweak it if desired
$ 
Description ('this is a test ticket'): # Existing description is automatically filled in here, user can just tweak it if desired
$ 
Type ('fix'): fix # Validate that the type the user entered is valid
Status ('active'): active # Validate that the status the user entered is valid
Tags ('test'): test # comma seperated
Select an option:
1) Return to search results
2) Return to main menu
$ 2
```
