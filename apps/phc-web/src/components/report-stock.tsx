"use client";

import { useRef, useState } from "react";
import { Camera, FileText, ListChecks, Mic, Square, Volume2 } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { apiPost, apiPostForm } from "@/lib/api";
import { fmtNum } from "@/lib/format";
import { LANGS, t, type Lang } from "@/lib/i18n";
import type { Capture, ConfirmResult, StockRow } from "@/lib/types";

type Method = "voice" | "photo" | "text" | "form";

interface SpeechRecognitionLike {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((e: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  start: () => void;
  stop: () => void;
}
type SpeechCtor = new () => SpeechRecognitionLike;

function speechRecognition(): SpeechCtor | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as { SpeechRecognition?: SpeechCtor; webkitSpeechRecognition?: SpeechCtor };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

export async function speak(text: string, lang: Lang) {
  try {
    const res = await apiPost<{ mode: string; audio_base64: string | null; mime_type: string | null; lang_tag?: string }>(
      "/api/text-to-speech",
      { text, language: lang },
    );
    if (res.audio_base64) {
      await new Audio(`data:${res.mime_type};base64,${res.audio_base64}`).play();
      return;
    }
  } catch {
    /* fall through to browser speech */
  }
  if ("speechSynthesis" in window) {
    const u = new SpeechSynthesisUtterance(text);
    u.lang = LANGS.find((l) => l.id === lang)?.speech ?? "en-IN";
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(u);
    toast.info("Demo mode: browser speech synthesis (Cloud Text-to-Speech not configured)");
  }
}

async function svgToPng(url: string): Promise<Blob> {
  const img = new Image();
  img.src = url;
  await img.decode();
  const canvas = document.createElement("canvas");
  canvas.width = img.naturalWidth || 900;
  canvas.height = img.naturalHeight || 620;
  canvas.getContext("2d")!.drawImage(img, 0, 0, canvas.width, canvas.height);
  return new Promise((resolve, reject) => canvas.toBlob((b) => (b ? resolve(b) : reject(new Error("png"))), "image/png"));
}

export function ReportStock({
  facilityId,
  lang,
  stock,
  onSaved,
}: {
  facilityId: string;
  lang: Lang;
  stock: StockRow[];
  onSaved: (r: ConfirmResult) => void;
}) {
  const [method, setMethod] = useState<Method>("voice");
  const [busy, setBusy] = useState(false);
  const [capture, setCapture] = useState<Capture | null>(null);
  const [qty, setQty] = useState<Record<string, string>>({});
  const [text, setText] = useState("");
  const [recording, setRecording] = useState(false);
  const [liveText, setLiveText] = useState("");
  const [photoUrl, setPhotoUrl] = useState<string | null>(null);
  const [formQty, setFormQty] = useState<Record<string, string>>({});
  const recorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);
  const recog = useRef<SpeechRecognitionLike | null>(null);
  const liveRef = useRef("");

  function show(c: Capture) {
    setCapture(c);
    setQty(Object.fromEntries(c.items.filter((i) => i.drug_code).map((i) => [i.drug_code!, i.quantity == null ? "" : String(i.quantity)])));
  }

  async function run(fn: () => Promise<Capture>) {
    setBusy(true);
    try {
      show(await fn());
    } catch (e) {
      toast.error(String(e));
    } finally {
      setBusy(false);
    }
  }

  function sendVoice(audio: Blob | null, transcript: string) {
    const fd = new FormData();
    fd.set("facility_id", facilityId);
    fd.set("language", lang);
    if (transcript) fd.set("transcript", transcript);
    if (audio && audio.size > 0) fd.set("audio", audio, "report.webm");
    return run(() => apiPostForm<Capture>("/api/capture/voice", fd));
  }

  async function startRecording() {
    setLiveText("");
    liveRef.current = "";
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      chunks.current = [];
      mr.ondataavailable = (e) => chunks.current.push(e.data);
      mr.onstop = () => {
        stream.getTracks().forEach((tr) => tr.stop());
        void sendVoice(new Blob(chunks.current, { type: mr.mimeType || "audio/webm" }), liveRef.current);
      };
      recorder.current = mr;
      mr.start();
      const Ctor = speechRecognition();
      if (Ctor) {
        const r = new Ctor();
        r.lang = LANGS.find((l) => l.id === lang)?.speech ?? "en-IN";
        r.continuous = true;
        r.interimResults = true;
        r.onresult = (e) => {
          const s = Array.from(e.results).map((res) => res[0].transcript).join(" ");
          liveRef.current = s;
          setLiveText(s);
        };
        r.start();
        recog.current = r;
      }
      setRecording(true);
    } catch {
      toast.error("Microphone unavailable. Using the sample voice report instead.");
      void sendVoice(null, "");
    }
  }

  function stopRecording() {
    recog.current?.stop();
    recog.current = null;
    recorder.current?.stop();
    recorder.current = null;
    setRecording(false);
  }

  function sendPhoto(file: Blob, preview: string) {
    setPhotoUrl(preview);
    const fd = new FormData();
    fd.set("facility_id", facilityId);
    fd.set("language", lang);
    fd.set("image", file, "register.png");
    return run(() => apiPostForm<Capture>("/api/capture/photo", fd));
  }

  async function confirm() {
    if (!capture) return;
    const items = capture.items
      .filter((i) => i.drug_code && qty[i.drug_code] !== "" && qty[i.drug_code] != null)
      .map((i) => ({ drug_code: i.drug_code!, quantity: Number(qty[i.drug_code!]), spoken_name: i.spoken_name }));
    if (!items.length) {
      toast.error("Enter at least one quantity");
      return;
    }
    setBusy(true);
    try {
      const res = await apiPost<ConfirmResult>(`/api/capture/${capture.capture_id}/confirm`, { items, confirmed_by: "PHC staff" });
      toast.success(res.message);
      setCapture(null);
      setPhotoUrl(null);
      setText("");
      onSaved(res);
    } catch (e) {
      toast.error(String(e));
    } finally {
      setBusy(false);
    }
  }

  const methods: { id: Method; icon: React.ReactNode }[] = [
    { id: "voice", icon: <Mic /> },
    { id: "photo", icon: <Camera /> },
    { id: "text", icon: <FileText /> },
    { id: "form", icon: <ListChecks /> },
  ];

  if (capture) {
    const prov = capture.provenance;
    return (
      <Card>
        <CardHeader>
          <CardTitle>{t("confirmTitle", lang)}</CardTitle>
          <CardDescription className="flex flex-wrap items-center gap-1.5">
            <span>{t("aiNote", lang)}</span>
            <Badge variant="outline" className="font-mono text-[10px]">
              {prov.model_name} · {prov.model_version} · {prov.prompt_version}
            </Badge>
            {prov.is_demo && <Badge className="bg-violet-100 text-violet-900">Demo AI ({prov.mode})</Badge>}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {capture.transcript?.transcript && capture.source === "voice" && (
            <div className="rounded-md bg-muted p-3 text-sm">
              <div className="mb-1 flex items-center gap-2 text-xs text-muted-foreground">
                {t("transcript", lang)} · {capture.transcript.provider}
                {capture.transcript.is_demo && <Badge className="bg-violet-100 text-violet-900">demo transcript</Badge>}
              </div>
              {capture.transcript.transcript}
            </div>
          )}
          {photoUrl && capture.source === "photo" && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={photoUrl} alt="Register page" className="max-h-56 rounded-md border object-contain" />
          )}
          {capture.rows && (
            <div className="overflow-x-auto">
              <p className="mb-1 text-xs font-medium text-muted-foreground">
                {t("registerRows", lang)} {capture.register_date ? `· ${capture.register_date}` : ""}
              </p>
              <table className="w-full text-xs">
                <thead className="text-muted-foreground">
                  <tr className="text-left">
                    <th className="py-1 pr-2">{t("heard", lang)}</th>
                    <th className="pr-2">Open</th>
                    <th className="pr-2">Recv</th>
                    <th className="pr-2">Issued</th>
                    <th>Closing</th>
                  </tr>
                </thead>
                <tbody>
                  {capture.rows.map((r) => (
                    <tr key={r.medicine_text} className={r.drug_code ? "" : "text-muted-foreground line-through"}>
                      <td className="py-0.5 pr-2">{r.medicine_text}</td>
                      {(["opening", "received", "issued", "closing"] as const).map((k) => (
                        <td key={k} className="pr-2">
                          {r[k] == null ? <span className="text-red-600">{t("illegible", lang)}</span> : fmtNum(r[k])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-xs text-muted-foreground">
                <tr className="text-left">
                  <th className="py-1 pr-2">{t("medicine", lang)}</th>
                  <th className="pr-2">{t("heard", lang)}</th>
                  <th className="pr-2 text-right">{t("current", lang)}</th>
                  <th className="pr-2">{t("newQty", lang)}</th>
                  <th className="text-right">{t("confidence", lang)}</th>
                </tr>
              </thead>
              <tbody>
                {capture.items
                  .filter((i) => i.drug_code)
                  .map((i) => (
                    <tr key={i.drug_code} className="border-t">
                      <td className="py-1.5 pr-2 font-medium">{i.standard_name}</td>
                      <td className="pr-2 text-muted-foreground">{i.spoken_name}</td>
                      <td className="pr-2 text-right tabular-nums">{fmtNum(i.current_on_hand)}</td>
                      <td className="pr-2">
                        <Input
                          type="number"
                          min={0}
                          inputMode="numeric"
                          aria-label={`${i.standard_name} ${t("newQty", lang)}`}
                          className={`h-8 w-24 ${qty[i.drug_code!] === "" ? "border-amber-500" : ""}`}
                          value={qty[i.drug_code!] ?? ""}
                          onChange={(e) => setQty((q) => ({ ...q, [i.drug_code!]: e.target.value }))}
                        />
                      </td>
                      <td className="text-right tabular-nums">
                        {Math.round(i.match_confidence * 100)}%
                        {i.needs_review && <Badge className="ml-1 bg-amber-100 text-amber-900">{t("review", lang)}</Badge>}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
          {capture.unrecognised.length > 0 && (
            <p className="rounded-md border border-amber-300 bg-amber-50 p-2 text-sm text-amber-900 dark:bg-amber-950 dark:text-amber-100">
              {t("unrecognised", lang)}: {capture.unrecognised.join(", ")}
            </p>
          )}
          <pre className="whitespace-pre-wrap rounded-md bg-muted/60 p-3 font-sans text-sm">{capture.confirmation_text}</pre>
          <div className="flex flex-wrap gap-2">
            <Button size="lg" onClick={confirm} disabled={busy}>
              {t("confirm", lang)}
            </Button>
            <Button size="lg" variant="outline" onClick={() => speak(capture.confirmation_text, lang)}>
              <Volume2 /> {t("play", lang)}
            </Button>
            <Button size="lg" variant="ghost" onClick={() => setCapture(null)} disabled={busy}>
              {t("cancel", lang)}
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("tabReport", lang)}</CardTitle>
        <div className="flex flex-wrap gap-1.5 pt-1" role="tablist">
          {methods.map((m) => (
            <Button
              key={m.id}
              role="tab"
              aria-selected={method === m.id}
              variant={method === m.id ? "default" : "outline"}
              size="lg"
              onClick={() => setMethod(m.id)}
            >
              {m.icon} {t(m.id, lang)}
            </Button>
          ))}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {method === "voice" && (
          <>
            <p className="text-sm text-muted-foreground">{t("voiceHint", lang)}</p>
            <div className="flex flex-wrap gap-2">
              {!recording ? (
                <Button size="lg" onClick={startRecording} disabled={busy} className="bg-red-600 text-white hover:bg-red-700">
                  <Mic /> {t("record", lang)}
                </Button>
              ) : (
                <Button size="lg" onClick={stopRecording} className="animate-pulse bg-red-600 text-white hover:bg-red-700">
                  <Square /> {t("stop", lang)}
                </Button>
              )}
              <Button size="lg" variant="outline" disabled={busy || recording} onClick={() => sendVoice(null, "")}>
                {t("sampleVoice", lang)}
              </Button>
            </div>
            {recording && (
              <p className="rounded-md bg-muted p-2 text-sm">
                {t("listening", lang)} {liveText}
              </p>
            )}
          </>
        )}
        {method === "photo" && (
          <div className="flex flex-wrap gap-2">
            <Button
              size="lg"
              variant="outline"
              disabled={busy}
              onClick={async () => sendPhoto(await svgToPng("/sample-register.svg"), "/sample-register.svg")}
            >
              {t("samplePhoto", lang)}
            </Button>
            <label className="inline-flex h-9 cursor-pointer items-center gap-1.5 rounded-lg bg-primary px-3 text-sm font-medium text-primary-foreground">
              <Camera className="size-4" /> {t("uploadPhoto", lang)}
              <input
                type="file"
                accept="image/*"
                capture="environment"
                className="sr-only"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) void sendPhoto(f, URL.createObjectURL(f));
                }}
              />
            </label>
          </div>
        )}
        {method === "text" && (
          <div className="space-y-2">
            <Textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder={t("textPlaceholder", lang)}
              rows={3}
              aria-label={t("text", lang)}
            />
            <Button
              size="lg"
              disabled={busy || !text.trim()}
              onClick={() => run(() => apiPost<Capture>("/api/capture/text", { facility_id: facilityId, text, language: lang }))}
            >
              {t("extract", lang)}
            </Button>
          </div>
        )}
        {method === "form" && (
          <div className="space-y-2">
            <div className="grid gap-2 sm:grid-cols-2">
              {stock.map((r) => (
                <label key={r.drug_code} className="flex items-center justify-between gap-2 rounded-md border p-2 text-sm">
                  <span>
                    {r.name} {r.strength}
                    <span className="block text-xs text-muted-foreground">
                      {t("current", lang)}: {fmtNum(r.on_hand)} {r.unit}s
                    </span>
                  </span>
                  <Input
                    type="number"
                    min={0}
                    className="h-8 w-24"
                    value={formQty[r.drug_code] ?? ""}
                    onChange={(e) => setFormQty((q) => ({ ...q, [r.drug_code]: e.target.value }))}
                  />
                </label>
              ))}
            </div>
            <Button
              size="lg"
              disabled={busy || !Object.values(formQty).some((v) => v !== "")}
              onClick={() =>
                run(() =>
                  apiPost<Capture>("/api/capture/form", {
                    facility_id: facilityId,
                    language: lang,
                    items: Object.entries(formQty)
                      .filter(([, v]) => v !== "")
                      .map(([drug_code, v]) => ({ drug_code, quantity: Number(v) })),
                  }),
                )
              }
            >
              {t("formSubmit", lang)}
            </Button>
          </div>
        )}
        {busy && <p className="text-sm text-muted-foreground">{t("working", lang)}</p>}
      </CardContent>
    </Card>
  );
}
