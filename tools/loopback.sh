cat defcon_contest_hashes.txt | grep -E ^[a-z_0-9]+:[0-9]+:[0-9A-F]{32}:[0-9A-F]{32}:::$ | grep -v AAD3B435B51404EEAAD3B435B51404EE > lm.txt
./john --format=NT --pot=cracked/NT.pot --loopback=cracked/LM.pot --rules=NT lm.txt
./john --format=NT --pot=cracked/NT.pot --loopback=cracked/LM.pot --rules=NT defcon_contest_hashes.txt
mv cracked/NT.pot tmp; cat tmp | sort > cracked/NT.pot; rm tmp
