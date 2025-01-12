import json
from flask import current_app
from github import Repository, PullRequest, PullRequestComment
from github.GithubException import GithubException
from typing import Dict, List
from src.settings import SCAN_CONTEXT, APP_REPO


def get_changed_files(
    repo: Repository,
    pr: PullRequest
) -> List[Dict[str, str]]:

    # Requires Repository Permissions: Pull requests -> Read
    files = pr.get_files()
    changed_files = []

    for file in files:
        if hasattr(file, 'patch') and '+0,0' not in file.patch:
            try:
                # Requires Repository Permissions: Contents -> Read
                full_file_content = repo.get_contents(
                    file.filename,
                    ref=pr.head.sha
                ).decoded_content.decode('utf-8')

                changed_files.append({
                    "filename": file.filename,
                    "diff": file.patch,
                    "full_content": full_file_content
                })

            except KeyError as e:
                current_app.logger.error(
                    f"Missing key in {repo.name}/{file.filename}, {file}: {e}"
                )
            except GithubException as e:
                current_app.logger.error(
                    f"GitHub API error: {e}"
                )
            except UnicodeDecodeError as e:
                current_app.logger.error(
                    f"Error decoding file content for {repo.name}/{file.filename}: {e}"
                )

    return changed_files


def determine_scan_status(
    scan_results: List[Dict[str, str]],
    pr: PullRequest,
    repo: Repository
) -> tuple:
    if scan_results:
        status = "failure"
        description = "Malware-in-code scan detected something. See new code comments."
        comment = comment_detections(scan_results, pr, repo)
        current_app.logger.info(f"PR #{pr.number} scan found: {json.dumps(scan_results)}")
        return status, description, comment
    else:
        status = "success"
        description = "Malware-in-code scan passed."
        return status, description


def comment_detections(
    detections: List[Dict[str, str]],
    pr: PullRequest,
    repo: Repository
) -> PullRequestComment:
    landmark_string = f"{repo.full_name}, PR #{pr.number}"
    comment = None
    for detection in detections:
        try:
            landmark_string = (
                f"{repo.full_name}/{detection['filename']}, "
                f"PR #{pr.number} line {str(detection['line_number'])}"
            )

            image_source = "https://avatars.githubusercontent.com/u/48519090?s=30&v=4"
            logo = f"[![Logo]({image_source})]({APP_REPO})"
            body = "\n".join([
                f"### {logo} Suspicious code detected ###",
                f"**Detected:** {detection['detection']}",
                f"**File:** {detection['filename']}",
                f"**Line:** {str(detection['line_number'])}",
                f"**Severity:** {detection['severity']}",
                *[
                    f"**{key}:** {value}" for key, value in detection.items()
                    if key not in ['detection', 'severity', 'line_number', 'filename']
                ]
            ])

            # Requires Repository Permissions: Pull requests -> Read and write
            comment = pr.create_review_comment(
                body=body,
                commit=repo.get_commit(pr.head.sha),
                path=detection['filename'],
                line=detection['line_number']
            )
            current_app.logger.info(
                f"Comment posted on {landmark_string}"
            )

        except KeyError as e:
            current_app.logger.error(
                f"Missing expected key in detection in {landmark_string}: {e}"
            )
        except ValueError as e:
            current_app.logger.error(
                f"Invalid value encountered while posting comment for {landmark_string}: {e}"
            )
        except GithubException as e:
            current_app.logger.error(
                f"GitHub API error commenting on {landmark_string}: {e}"
            )

    return comment


def create_commit_status(
    repo: Repository,
    commit_sha: str,
    status: str,
    description: str,
    target_url: str = 'https://github.com/apiiro/pr-event'
):
    try:
        commit = repo.get_commit(commit_sha)
        commit.create_status(
            context=SCAN_CONTEXT,
            state=status,
            description=description,
            target_url=target_url
        )
    except GithubException as e:
        current_app.logger.error(
            f"GitHub API error creating commit status for {commit_sha}: {e}"
        )
