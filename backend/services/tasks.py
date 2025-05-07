import httpx
import os
import asyncio
import json
import re
from datetime import datetime
from bson import ObjectId
from db.database import get_db
from dotenv import load_dotenv
from core.logger import get_logger
from core.constants import MeetingStatus, ActionItemStatus, AIModels

logger = get_logger(__name__)

load_dotenv()

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = os.getenv(
    "GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions"
)


async def upload_to_assemblyai(client: httpx.AsyncClient, file_path: str):
    headers = {"Authorization": ASSEMBLYAI_API_KEY}

    with open(file_path, "rb") as f:
        content = f.read()

    response = await client.post(
        "https://api.assemblyai.com/v2/upload", headers=headers, content=content
    )
    response.raise_for_status()
    return response.json()["upload_url"]


async def _submit_transcription_job(
    client: httpx.AsyncClient, upload_url: str, headers: dict
):
    logger.info("Starting transcription...")
    transcript_req = await client.post(
        "https://api.assemblyai.com/v2/transcript",
        json={
            "audio_url": upload_url,
            "speech_models": [AIModels.ASSEMBLYAI_SPEECH_MODEL],
            "speaker_labels": True,
        },
        headers=headers,
    )
    if transcript_req.status_code != 200:
        logger.error(f"Transcript Error: {transcript_req.text}")
        return None
    transcript_req.raise_for_status()
    return transcript_req.json()["id"]


async def _poll_transcription_status(
    client: httpx.AsyncClient, transcript_id: str, headers: dict
):
    logger.info(f"Polling transcription {transcript_id}...")
    while True:
        poll_req = await client.get(
            f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
            headers=headers,
        )
        poll_req.raise_for_status()
        status_data = poll_req.json()
        status = status_data["status"]

        if status == "completed":
            return status_data
        elif status == "error":
            logger.error(f"Transcription error: {status_data.get('error')}")
            return None

        await asyncio.sleep(3)


def _format_transcription_results(status_data: dict):
    utterances = status_data.get("utterances", [])
    words = status_data.get("words", [])
    segments = []
    transcript_text = status_data.get("text", "")

    if utterances:
        transcript_text = " ".join(
            [
                f"Speaker {u.get('speaker', 'Unknown')}: {u.get('text', '')}"
                for u in utterances
            ]
        )
        for u in utterances:
            segments.append(
                {
                    "start": u.get("start", 0),
                    "end": u.get("end", 0),
                    "text": u.get("text", ""),
                    "speaker": f"Speaker {u.get('speaker', 'Unknown')}",
                }
            )
    elif words:
        for i in range(0, len(words), 10):
            chunk = words[i : i + 10]
            segments.append(
                {
                    "start": chunk[0]["start"],
                    "end": chunk[-1]["end"],
                    "text": " ".join([w["text"] for w in chunk]),
                }
            )

    return transcript_text, segments


async def _transcribe_audio(file_path: str):
    transcript_text = "Transcription failed."
    segments = []
    status_success = False

    if not ASSEMBLYAI_API_KEY or not os.path.exists(file_path):
        return transcript_text, segments, False

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            headers = {"Authorization": ASSEMBLYAI_API_KEY}

            logger.info(f"Uploading {file_path} to AssemblyAI...")
            upload_url = await upload_to_assemblyai(client, file_path)

            transcript_id = await _submit_transcription_job(client, upload_url, headers)
            if not transcript_id:
                return transcript_text, segments, False

            status_data = await _poll_transcription_status(
                client, transcript_id, headers
            )

            if status_data:
                transcript_text, segments = _format_transcription_results(status_data)
                status_success = True

    except Exception as e:
        logger.error(f"AssemblyAI processing error: {e}")
        transcript_text = "Transcription error occurred."

    return transcript_text, segments, status_success


async def _generate_summary(transcript_text: str):
    summary_text = f"Summary of: {transcript_text[:100]}..."
    key_points = []
    status_success = False

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            prompt = f"Summarize this meeting transcript and list key points:\n{transcript_text}"
            payload = {
                "model": AIModels.GROQ_LLM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            }
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
            logger.info(
                f"Sending request to Groq URL: {GROQ_API_URL} with payload: {payload}"
            )
            response = await client.post(GROQ_API_URL, json=payload, headers=headers)
            logger.info(f"Groq response status: {response.status_code}")
            logger.info(f"Groq response text: {response.text}")

            if response.status_code == 200:
                data = response.json()
                summary_text = data["choices"][0]["message"]["content"]
                key_points = ["See summary text for details."]
                status_success = True
            else:
                logger.error(f"Groq returned non-200 status: {response.status_code}")
                summary_text = "AI processing failed"
    except Exception as e:
        logger.error(f"Groq not available or failed for summary. Error: {e}")
        summary_text = "AI processing failed"

    return summary_text, key_points, status_success


async def _extract_action_items(transcript_text: str):
    action_item_desc = "Review transcript for action items."
    assignee = None
    status_success = False

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            prompt = (
                f"Extract a single clear action item from this text and determine who is responsible based on the speaker labels. "
                f"Return your answer as a JSON object strictly following this structure: "
                f'{{"description": "...", "assignee": "Speaker A"}}\n\n'
                f"Text:\n{transcript_text}"
            )
            payload = {
                "model": AIModels.GROQ_LLM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            }
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
            logger.info(
                f"Sending action item request to Groq URL: {GROQ_API_URL} with payload: {payload}"
            )
            response = await client.post(GROQ_API_URL, json=payload, headers=headers)
            logger.info(f"Groq action item response status: {response.status_code}")
            logger.info(f"Groq action item response text: {response.text}")

            if response.status_code == 200:
                data = response.json()
                response_text = data["choices"][0]["message"]["content"].strip()

                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                if json_match:
                    try:
                        parsed = json.loads(json_match.group(0))
                        action_item_desc = parsed.get("description", action_item_desc)
                        assignee = parsed.get("assignee")
                    except json.JSONDecodeError:
                        action_item_desc = response_text
                else:
                    action_item_desc = response_text
                status_success = True
            else:
                logger.error(f"Groq action item non-200 status: {response.status_code}")
    except Exception as e:
        logger.error(f"Groq failed for action items. Error: {e}")

    return action_item_desc, assignee, status_success


async def process_meeting_audio(meeting_id: str):
    db = get_db()

    # Wait a tiny bit to ensure the DB record is there if needed
    await asyncio.sleep(1)

    # Find meeting
    meeting = await db.meetings.find_one({"_id": ObjectId(meeting_id)})
    if not meeting:
        logger.warning(f"Meeting {meeting_id} not found.")
        return

    audio_path = meeting.get("audioFilePath", "").lstrip("/")
    file_path = os.path.join(os.path.dirname(__file__), audio_path)

    overall_status = MeetingStatus.COMPLETED

    transcript_text, segments, trans_success = await _transcribe_audio(file_path)
    if not trans_success:
        overall_status = MeetingStatus.ERROR

    # Save transcript
    transcript_doc = {
        "meetingId": ObjectId(meeting_id),
        "content": transcript_text,
        "timestampedSegments": segments,
        "generatedAt": datetime.utcnow(),
    }
    await db.transcripts.insert_one(transcript_doc)

    summary_text, key_points, sum_success = await _generate_summary(transcript_text)
    if not sum_success:
        overall_status = MeetingStatus.ERROR

    summary_doc = {
        "meetingId": ObjectId(meeting_id),
        "summaryText": summary_text,
        "keyPoints": key_points,
        "originalVersion": summary_text,
        "generatedAt": datetime.utcnow(),
    }
    await db.summaries.insert_one(summary_doc)

    action_item_desc, assignee, action_success = await _extract_action_items(
        transcript_text
    )
    if not action_success:
        overall_status = MeetingStatus.ERROR

    action_item_doc = {
        "meetingId": ObjectId(meeting_id),
        "ownerId": meeting["ownerId"],
        "description": action_item_desc,
        "assignee": assignee,
        "status": ActionItemStatus.PENDING,
        "source": "ai-generated",
    }
    await db.actionItems.insert_one(action_item_doc)

    # Update meeting status
    await db.meetings.update_one(
        {"_id": ObjectId(meeting_id)}, {"$set": {"status": overall_status}}
    )
    logger.info(
        f"Processing finished for meeting {meeting_id} with status {overall_status}"
    )
