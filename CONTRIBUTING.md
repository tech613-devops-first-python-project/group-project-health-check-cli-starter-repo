# How this team works

Read this before anyone writes any code. Ten minutes now saves an hour at four
o'clock.

You are learning Git at the same time as you are using it for real, on a shared
repository, with a deadline. That is uncomfortable and it is deliberate. The
friction is the lesson.

## Roles

Pick these in the first ten minutes. Everyone holding a role still writes code;
none of these is a manager.

**Git lead.** Creates the team repository, sets up branch protection, and is the
first port of call when a merge goes wrong. Not the only person allowed to merge,
just the person who has read the instructions twice. *Oliver.*

**Scrum Master.** Facilitates. Runs the stand-up, keeps the board honest, and
protects the team's time. Facilitating is not deciding, and it is not doing
everyone's admin. *Jackson.*

**Development lead.** Owns `healthcheck.py` and keeps an eye on how the pieces
fit together, so that the HTTP check and the disk check agree on how the health
response gets passed between them. *Nowres.*

Everyone else is a developer, which is also what the three above are. Do not
invent roles to fill seats.

## Splitting the work

This project splits cleanly, which is why it suits a group. One person per
module:

| Module | Tier | Adds to `targets.yaml` |
|---|---|---|
| `config.py` | Core | `timeout_seconds` under `defaults`, and validates everything the others add |
| `checks/tcp.py` | Core | `port` on every target |
| `checks/http.py` | Extension | `health_url` on every target |
| `checks/disk.py` | Extension | `disk_threshold_percent` under `defaults` |
| `report.py` | Core, then extension | Nothing |
| `checks/ping.py`, `alerts.py` | Stretch | Nothing |

There are more modules than people, so in a group of three or four someone
takes two. Agree it on the board, not by everyone quietly starting on the same
file.

Every check returns a `CheckResult`, defined in `checks/__init__.py`. That file
is the agreement that lets you work apart and still fit together. Do not change
its shape without telling the whole team.

## Setting up the repository (Complete)

The Git lead does this once, before anyone clones.

1. Create the repository from the template your trainer gives you.
2. Add everyone else as a collaborator with write access.
3. Protect `main`, so nothing lands without a review:
   - Settings, then Branches, then Add branch ruleset
   - Target the `main` branch
   - Tick **Require a pull request before merging**
   - Tick **Require approvals**, set to 1
   - Tick **Block force pushes** and **Restrict deletions**

Branch protection on a free account needs the repository to be public. Check with
your trainer before making anything public.

Protecting `main` is not bureaucracy. It is what stops one person's broken commit
from blocking four other people at the worst possible moment.

## The workflow

One branch per story.

```bash
git checkout main
git pull
git checkout -b check-http

# ... work, commit as you go ...

git push -u origin check-http
```

Then open a pull request, ask someone to review it, and merge it once they have
approved. Then everyone else pulls `main` and brings it into their branch:

```bash
git checkout my-branch
git merge main
```

Do that often. The longer a branch lives away from `main`, the worse the merge
gets.

Worth discussing as a team once you are comfortable: could you use `git rebase`
here instead, and what would change?

## Reviewing a pull request

Every change needs one approval before it merges. A review is not a formality,
and "looks good to me" thirty seconds after the notification is not a review.

Read the code and ask:

- Does it do what the pull request says it does?
- Does every network call have a timeout?
- Would it crash on the obvious bad input: a missing key, a target that does not
  exist, a response that is not JSON?
- Are there tests, and would they fail if the code were wrong? Try it: break the
  code on purpose and run them.
- Could you maintain this in a fortnight?

Say what is good as well as what is wrong. You will all be on the receiving end
of this by the end of the day.

If the change was drafted with AI, the reviewer's job gets more important, not
less. Ask the author to explain what it does before you approve it.

## Merge conflicts

You will get one on `targets.yaml`. Every check needs its own key, and the TCP,
HTTP, disk and timeout work will all add lines next to each other on different
branches. Expect it. It is not a sign anyone did anything wrong. It means the
plan is working.

When it happens:

1. Do not panic and do not delete the branch.
2. Resolve it **locally**, not in the browser. You have better tools and you can
   run the tool and the tests afterwards.
3. Open the file. Git has marked both versions between `<<<<<<<` and `>>>>>>>`.
   In this file you almost always want **both** sides: one branch added `port`,
   the other added `health_url`, and the target needs both. Keep both lines,
   delete the markers, and save.
4. Check the YAML still parses and the tool still runs:
   `python healthcheck.py`. Indentation is the usual casualty.
5. Run the tests before you commit the resolution.
6. Tell the team what you did, so nobody reapplies a change you removed.

The best way to handle conflicts is to have fewer of them. Pull from `main`
often, keep branches short, and agree who is changing `targets.yaml` and when.

## Secrets

The stretch-tier webhook URL goes in the `HEALTHCHECK_WEBHOOK_URL` environment
variable. Never in `targets.yaml`, never in code, never in a commit message.
`.env` is already in `.gitignore`.

If a secret is ever committed, deleting it in the next commit does not remove it.
It is still in the history, and anyone can read it. The fix is to change the
secret. Tell your trainer straight away.

## Definition of ready

A story is ready to pick up when it has acceptance criteria, everyone agrees what
"done" means for it, and it does not depend on something nobody has started.

## Definition of done

A story is done when the code works, a test covers it, someone else has reviewed
it, and it is merged into `main`. Not when it works on your laptop.

## Stand-up

Ten minutes, standing. What you did, what you are doing, what is blocking you.
Blockers go to the Scrum Master to clear. Anything that needs a real discussion
gets taken outside the stand-up rather than eating everyone's morning.
