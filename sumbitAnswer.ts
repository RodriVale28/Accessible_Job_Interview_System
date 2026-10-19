// S1-3.2 Submit answer -> save -> next question — owner: Jayme Nguyen
export type SubmitResult = {
  nextQuestion?: { id: number; prompt: string };
  qIndex: number;
  total: number;
  completed: boolean;
};

export async function submitAnswer(
  sessionId: number,
  questionId: number,
  text: string
): Promise<SubmitResult> {
  try {
    // 1. Send the answer to the backend
    const response = await fetch(
      `/api/sessions/${sessionId}/answer`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          question_id: questionId,
          answer: text,
        }),
      }
    );

    // 2. Handle errors from the backend
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));

      throw new Error(
        errorData.error || "The AI could not analyze that answer."
      );
    }

    // 3. Read the backend response
    const data = await response.json();

    if (typeof data.is_last !== "boolean") {
      throw new Error("Invalid response from the server.");
    }

    // 4. Prepare the next question, if there is one
    let nextQuestion: SubmitResult["nextQuestion"];

    if (!data.is_last) {
      if (
        typeof data.next_question_id !== "number" ||
        typeof data.next_question !== "string"
      ) {
        throw new Error("The next question is missing from the response.");
      }

      nextQuestion = {
        id: data.next_question_id,
        prompt: data.next_question,
      };
    }

    // 5. Return the interview state
    return {
      nextQuestion,
      qIndex: data.q_index,
      total: data.total,
      completed: data.is_last,
    };
  } catch (err: unknown) {
    // 6. Show a retry message if the request fails
    const message =
      err instanceof Error ? err.message : "Network error";

    throw new Error(`${message} (tap send to retry)`);
  }
}
