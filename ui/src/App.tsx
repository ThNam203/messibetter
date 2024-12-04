"use client";

import { useEffect, useState } from "react";
import { Upload, AlertCircle } from "lucide-react";
import { Button } from "./components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "./components/ui/card";
import { Checkbox } from "./components/ui/checkbox";
import { Alert, AlertDescription } from "./components/ui/alert";
import { Label } from "./components/ui/label";
import "./index.css";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "./components/ui/table";

const EDIT_OPTIONS = ["SPT", "LPT", "WSPT", "EDD", "SRPT", "LST", "LRPT"];

export default function App() {
    const [file, setFile] = useState<File | null>(null);
    const [selectedOptions, setSelectedOptions] = useState<string[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [results, setResults] = useState<any>(null);

    // chon va doi file excel
    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = event.target.files?.[0];
        if (
            selectedFile &&
            selectedFile.type ===
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ) {
            setFile(selectedFile);
            setError(null);
        } else {
            setFile(null);
            setError("Please select a valid Excel file (.xlsx)");
        }
    };

    // dieu khien chon option
    const handleOptionToggle = (option: string) => {
        setSelectedOptions((prev) =>
            prev.includes(option)
                ? prev.filter((item) => item !== option)
                : [...prev, option]
        );
    };

    // xu ly cac lua chon -> gui backend
    const handleExecuteRules = async () => {
        if (!file) {
            setError("Please upload an Excel file first");
            return;
        }
        if (selectedOptions.length === 0) {
            setError("Please select at least one rule to execute");
            return;
        }

        setError(null);
        setResults(null);

        // Sort selected options based on their order in EDIT_OPTIONS
        const sortedOptions = [...selectedOptions].sort(
            (a, b) => EDIT_OPTIONS.indexOf(a) - EDIT_OPTIONS.indexOf(b)
        );

        const formData = new FormData();
        formData.append("file", file);
        formData.append("mode", "execute"); // Add mode parameter
        sortedOptions.forEach((option) => {
            formData.append("rules", option);
        });

        try {
            const response = await fetch("http://localhost:5000/process", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                setError(
                    errorData.error ||
                        "An error occurred while processing the file."
                );
                return;
            }

            const result = await response.json();
            setResults(result);
        } catch (error) {
            setError(
                "Failed to connect to the server. Please try again later."
            );
            console.error("Upload error:", error);
        }
    };

    const handleCompareRules = async () => {
        if (!file) {
            setError("Please upload an Excel file first");
            return;
        }
        if (selectedOptions.length < 2) {
            setError("Please select at least two rules to compare");
            return;
        }

        setError(null);
        setResults(null);

        // Sort selected options based on their order in EDIT_OPTIONS
        const sortedOptions = [...selectedOptions].sort(
            (a, b) => EDIT_OPTIONS.indexOf(a) - EDIT_OPTIONS.indexOf(b)
        );

        const formData = new FormData();
        formData.append("file", file);
        formData.append("mode", "compare"); // Add mode parameter
        sortedOptions.forEach((option) => {
            formData.append("rules", option);
        });

        try {
            const response = await fetch("http://localhost:5000/process", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                setError(
                    errorData.error ||
                        "An error occurred while processing the file."
                );
                return;
            }

            const result = await response.json();
            setResults(result);
        } catch (error) {
            setError(
                "Failed to connect to the server. Please try again later."
            );
            console.error("Upload error:", error);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-b from-gray-100 to-gray-200 flex items-center justify-center space-x-4">
            <Card className="w-full max-w-2xl">
                <CardHeader>
                    <CardTitle>Dispatching Rule Selector</CardTitle>
                    <CardDescription>
                        Upload an Excel file and choose editing options
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    <div className="space-y-2">
                        <Label htmlFor="file-upload">Upload Excel File</Label>
                        <div className="flex items-center justify-center w-full">
                            <label
                                htmlFor="file-upload"
                                className="flex flex-col items-center justify-center w-full h-64 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100"
                            >
                                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                    <Upload className="w-8 h-8 mb-4 text-gray-500" />
                                    <p className="mb-2 text-sm text-gray-500 font-semibold">
                                        Click to upload
                                    </p>
                                    <p className="text-xs text-gray-500">
                                        Excel file (XLSX)
                                    </p>
                                </div>
                                <input
                                    id="file-upload"
                                    type="file"
                                    className="hidden"
                                    onChange={handleFileChange}
                                    accept=".xlsx"
                                />
                            </label>
                        </div>
                        {file && (
                            <p className="text-sm font-bold text-green-600">
                                File uploaded: {file.name}
                            </p>
                        )}
                    </div>
                    <div className="space-y-2">
                        <Label>Editing Options</Label>
                        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
                            {EDIT_OPTIONS.map((option) => (
                                <div
                                    key={option}
                                    className="flex items-center space-x-2"
                                >
                                    <Checkbox
                                        id={option}
                                        checked={selectedOptions.includes(
                                            option
                                        )}
                                        onCheckedChange={() =>
                                            handleOptionToggle(option)
                                        }
                                    />
                                    <Label htmlFor={option}>{option}</Label>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className="flex flex-col sm:flex-row gap-4">
                        <Button
                            onClick={handleExecuteRules}
                            variant="outline"
                            className="flex-1"
                        >
                            Execute selected rules
                        </Button>
                        <Button
                            onClick={handleCompareRules}
                            variant="outline"
                            className="flex-1"
                        >
                            Compare rules
                        </Button>
                        {results && (
                            <Button
                                onClick={() => {
                                    setResults(null);
                                    setSelectedOptions([]);
                                }}
                                variant="destructive"
                                className="flex-1 font-bold"
                            >
                                Remove results
                            </Button>
                        )}
                    </div>
                    {error && (
                        <Alert variant="destructive">
                            <div className="flex items-center space-x-8">
                                <AlertCircle className="h-4 w-4" />
                                <AlertDescription>{error}</AlertDescription>
                            </div>
                        </Alert>
                    )}
                </CardContent>
            </Card>

            {results && (
                <div className="flex flex-col h-[95vh] space-y-4 overflow-y-auto">
                    {results.compare_data && (
                        <Card>
                            <CardHeader>
                                <CardTitle>Compare result</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-6 max-h-screen">
                                <CompareTable data={results.compare_data} />
                            </CardContent>
                        </Card>
                    )}
                    {results.results.map((result: any) => (
                        <Card>
                            <CardHeader>
                                <CardTitle>{result.rule}</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-6 max-h-screen">
                                <GanttChartAndTable
                                    data={result.schedule}
                                    image={result.gantt_chart}
                                />
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
}

function GanttChartAndTable({ data, image }: { data: any[]; image: string }) {
    return (
        <div style={{ height: "300px" }} className="flex flex-row space-x-4">
            <img
                className="max-w-2xl"
                src={"data:image/png;base64, " + image}
                alt="image"
            />
            <Table className="w-[300px] border-[1px]">
                <TableHeader>
                    <TableRow>
                        <TableHead>Job</TableHead>
                        <TableHead>Release Time</TableHead>
                        <TableHead>Processing Time</TableHead>
                        <TableHead>Start Time</TableHead>
                        <TableHead>Completion Time</TableHead>
                        <TableHead>Flow Time</TableHead>
                        <TableHead>Late Time</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {data.map((item, index) => (
                        <TableRow key={index}>
                            <TableCell className="font-medium">
                                {item.job}
                            </TableCell>
                            <TableCell>{item["rj"]}</TableCell>
                            <TableCell>{item["pj"]}</TableCell>
                            <TableCell>{item["Start time"]}</TableCell>
                            <TableCell>{item["Completion time"]}</TableCell>
                            <TableCell>{item["Flow time"]}</TableCell>
                            <TableCell>{item["Late time"]}</TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
    );
}

function CompareTable({ data }: { data: any[] }) {
    return (
        <div className="flex flex-row space-x-4">
            <Table className="w-full border-[1px]">
                <TableHeader>
                    <TableRow>
                        <TableHead>Rule</TableHead>
                        <TableHead>Average Completion Time</TableHead>
                        <TableHead>Average Flow Time</TableHead>
                        <TableHead>Average Late Time</TableHead>
                        <TableHead>Utilization (%)</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {data.map((item, index) => (
                        <TableRow key={index}>
                            <TableCell className="font-medium">
                                {item["Rule"]}
                            </TableCell>
                            <TableCell>
                                {item["Average Completion Time"]}
                            </TableCell>
                            <TableCell>{item["Average Flow Time"]}</TableCell>
                            <TableCell>{item["Average Late Time"]}</TableCell>
                            <TableCell>{item["Utilization (%)"]}</TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
    );
}
