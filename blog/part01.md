# Creating JTR rules

For this exercise I will be walking you through the steps that I took to attempt the Korelogic Crack-Me-If-You-Can 2010 challenge.  The challenge
was part of DEFCON and contestants were given a large file with hashes to crack as quickly as possible.  The basis for this was used to create a
series of official JTR rules, but I wanted to start a zero-knowledge approach to this where we buiild out the rules as we need them, and also 
collect and create wordlists as they are required.

## Setting up
I custom built a copy of john and downloaded the hashfile (defcon_contest_hashes.txt) alongside an empty john.conf file.  That's it. All tools utilized 
moving forward are of my own creation.

## Initial Analysis
The hashfile has 54680 lines in it, and looking at the contents, it looks to be varying hashtypes.  Some hashes are trivial to crack while others
take excessive power. We would obviously go for the easier ones to begin with, and go from there.

A tool that I wrote (tools/hash_identifier.py) attempts to identify what kind of hashes are contained in the hashfile.  Results are:

- NTLM - 30821
- Salted-SHA1 - 10582
- descrypt - 7155
- md5crypt - 4716
- mysql? - 1000
- Raw-SHA1 - 326
- bcrypt - 80


Taking information of [a test run](http://www.admin-magazine.com/Articles/John-the-Ripper) compares the cracking speed of some of the above:

Hashes per second:
- NTLM - 10635K
- Salted-SHA1 - 3720K
- descrypt - 1300k
- Raw-SHA1 - 3749k


For now, given the speed and popularity of NTLM, we should look into attacking this first.

## NTLM hashes

NTLM hashes look like the following:
`jpaluck:1000:AAD3B435B51404EEAAD3B435B51404EE:67BE9A1F59171642F34C0215ABDF28DD:::`

The follow the form of `username:userid:LM HASH:NT HASH:::`. The LM hash is a legacy algorithm found in 
XP and before, but is now outdated and inscecure.  The NT hash is its replacement but the LM hash is kept for
legacy reasons.  In newer versions of Windows, the LM hash is blank (_AAD3B435B51404EEAAD3B435B51404EE_) but if
we can find any NTLM hashes with populated LM hashes, we can crack those and move to cracking the NT hashes with the 
information gathered.

## LM hashes vs NT hashes
NT hashes are a standard hashing format but not trivial. There are no real limitations with NT hashes whereas LM hashes
have plenty.  Firstly, the LM hash is actually two smaller hashes joined together.  The password for LM is a maximum of
14 characters with it split into 7 characters and hashed accordingly. Also, the passwords are case insensitive. NT hashes have none of these limitations.

Having a confined set of possibilities for LM hashes makes them easy to crack, as they can only be a maximum of 7 chars
long, and they can only be a digit, symbol, or uppercase character.

So, the hash for `PASS123` is the same as `pass123`.  Also, as passes are split in two (chars[0-6], chars[7-13]), the first hash
for passes `pass1234` and `pass1234567` will be the same. These limitations will allow us to try all combinations
within a few hours. 

## Cracking all LM hashes
For this, let's extract all NTLM hashes with an LM hash embedded.  Let's use some regex to extract the NTLM hashes and filter out the empty LM hasehs.

`cat defcon_contest_hashes.txt | grep -E "$*:[0-9A-F]{32}:*:::$""" | grep -v AAD3B435B51404EEAAD3B435B51404EE > lm.txt`

Running this gives us 2552 NTLM hashes. We will bruteforce every combination of characters from 0 to 7 (uppercase, numbers and symbols) until we have 
cracked every LM hash.  While john can do brute forcing, at the minute it is not working as we have an empty john.conf file, so we will utilize another 
tool called _crunch_ to generate the words to try.  Note that for LM, we will be saving all cracked hashes in a special file called a _pot_.  The storage
location is at _cracked/LM.pot_.

So, to execute this, we run:
`crunch 0 7 -f /usr/share/crunch/charset.lst ualpha-numeric-all | ./john --stdin lm.txt --format=LM --pot=cracked/LM.pot`

This will take a few hours so let it do its thing.  According to john, there was a total of 3380 unique LM hashes. At the end of the run, all 3380 hashes will reside in the specified pot file.

Technically however, we have still not cracked a single hash in the file, but merely provided hints at what the values for the 2552 NT hashes are.  Luckily, john is excellent at joining the
LM hashes and attmepting them. First though, we need to write our first rule.

## Rule - 'NT'
In john.conf, we declare rules to tell them what to do with the word passed to it from a wordlist, and then perform some actions on it.  If we receive a cracked LM hash word, we need to try
all combinations of uppercase/lowercase in order to find the correct one.  The LM hash is almost always a case insensitive version of the NT hash, so we just take that word as our starting point.

If we had an LM hash of `ABC`, the NT hash must be one of the following:
- `abc`
- `abC`
- `aBc`
- `aBC`
- `Abc`
- `AbC`
- `ABc`
- `ABC`

The rule syntax to perform this is:
```
[List.Rules:NT]
:
-c T[z0]T[z1]T[z2]T[z3]T[z4]T[z5]T[z6]T[z7]T[z8]T[z9]T[zA]T[zB]T[zC]
```

The first line just declares the rule name, the second line `:` is a symbol saying "use the word as-is, with no changes".  The next line is a little complicated but can be understood if broken down. 
The `-c` tells john to skip this if the hashing format does not support case sensitivity.  The second character `T` is a case modifier. If we have a rule that just said `T0`, if would switch the case 
of the character at position 0 (start of word). For numbers over 9, letters are used (A == 10), etc. `TA` would switch the case at position 10.  If there is a non-alpha character at this position or if
the word is not that long, it is simply ignored.  

Sometimes we cant to ignore the rule and try it both uppercase and lowercase, in that instance, we add a `z` character.  This means it will toggle the character at the 'infinite' position, i.e. beyond the
end of the word.  By doing this, rule T[z0] will output 'apple' and 'Apple' for example.  We can also chain these permutations by adding further logic to the rule.  `T[z0]T[z1]` will try all permutations of 
the first two characters: `apple, Apple, aPple, APple`. This logic continues for the 14 characters that the LM hashes can make.

To run this rule, we use the `--rule` flag with john. Also, we can just reference the LM.pot file with all cracked LM passwords in a special commmand called a 'loopback'

The syntax to perform this is:

`./john --format=NT --pot=cracked/NT.pot --loopback=cracked/LM.pot --rules=NT lm.txt`

Note that we are now using the hash format 'NT' and cracking into a new pot.  This is not necessary normally but we will be keeping pots separate for this experiment. It seems that most if not all NT hashes are
cracked. Let's confirm by asking john to show the remaining hashes.

`./john lm.txt --format=NT --pot=cracked/NT.pot --show=left`

It appears that there is one password left:
```ariston:$NT$2bc71a6b90d86b1fa0c1714d5a590bd5

2556 password hashes cracked, 1 left
```

Looking into this, it seems that the password is over 14 characters old, so we only have the first 14 characters stored in LM, so the NT attempt fails.  For now, we can skip this and come back to it later.
Running this against the full hashfile is a good idea as it picks up other NT only hashes.

`./john --format=NT --pot=cracked/NT.pot --loopback=cracked/LM.pot --rules=NT defcon_contest_hashes.txt`

At the end of this, we should have 2561 NT hashes cracked. 

## NT Bruteforcing

Finally, I wanted to run a bruteforce against all NT hashes of lengths 0-6.  I once again used the crunch binary to generate the wordlist and pipe it into john, but this time I wrapped it in a piece of code
located in `tools/crunchbrute.sh`.  Usage is simple:

`./tools/crunchbrute.sh 0 6 NT`

At the end of this run we hade 3561 cracked NT hashes. Good start!

