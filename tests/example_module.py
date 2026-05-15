from userbank import UserBank

bank = UserBank.from_config()

raqa_users = bank.search(application="raqa")

for u in raqa_users:
    print(f"{u['UserName']:20} {u['Email']:30}")

# The search method also supports regex matching:
raqa_users = bank.search(application_re=r"raqa")

for u in raqa_users:
    print(u)

# The search method also supports regex matching:
raqa_users = bank.search(application_re=r"seek")

for u in raqa_users:
    print(u)