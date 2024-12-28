Dropzone.autoDiscover = false;

function init() {
    let dz = new Dropzone("#dropzone", {
        url: "/CLASSIFY_IMAGES", // Flask endpoint
        method: "post",
        maxFiles: 1,
        addRemoveLinks: true,
        dictDefaultMessage: "Drop an image here to classify",
        autoProcessQueue: false,
    });

    // Ensure only one file is uploaded at a time
    dz.on("addedfile", function (file) {
        if (dz.files[1] != null) {
            dz.removeFile(dz.files[0]);
        }

        // Read file as Base64 and assign to file.dataURL
        let reader = new FileReader();
        reader.onload = function (event) {
            file.dataURL = event.target.result; // Assign Base64 data
            console.log("Base64 data created:", file.dataURL);
        };
        reader.onerror = function (error) {
            console.error("Error reading file:", error);
        };
        reader.readAsDataURL(file);
    });

    $("#submitBtn").on("click", function (e) {
        e.preventDefault(); // Prevent default form submission
        if (dz.files.length === 0) {
            $("#error").text("Please upload an image before submitting.").show();
            return;
        }

    // Handle Dropzone "complete" event
    let file = dz.files[0];
    if (!file || !file.dataURL) {
            $("#error").text("No valid image data found.").show();
            return;
        }

        let imageData = file.dataURL; // Base64 encoded image
        let url = "/CLASSIFY_IMAGES"; // Flask endpoint

        // Prepare JSON payload for the POST request
        let payload = JSON.stringify({ image_data: imageData }); // Ensure key matches Flask backend expectation

        fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: payload,
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error("Failed to classify the image. Please try again.");
                }
                return response.json();
            })
            .then(data => {
                if (!data || data.length === 0) {
                    $("#resultHolder").hide();
                    $("#divClassTable").hide();
                    $("#error").text("No classification results returned.").show();
                    return;
                }

                // Process the classification results
                let match = null;
                let bestScore = -1;

                data.forEach(item => {
                    if (item.class_probability && Array.isArray(item.class_probability)) {
                        let maxScoreForThisClass = Math.max(...item.class_probability);
                        if (maxScoreForThisClass > bestScore) {
                            match = item;
                            bestScore = maxScoreForThisClass;
                        }
                    } else {
                        console.error("Error in classification:", item.error || "Invalid response");
                    }
                });

                if (match) {
                    $("#error").hide();
                    $("#resultHolder").show();
                    $("#divClassTable").show();
                    $("#resultHolder").html($(`[data-player="${match.class}"]`).html());

                    let classDictionary = match.class_dictionary;
                    for (let personName in classDictionary) {
                        let index = classDictionary[personName];
                        let probabilityScore = match.class_probability[index];
                        $(`#score_${personName}`).text(probabilityScore.toFixed(2)); // Ensure score format
                    }
                } else {
                    $("#error").text("No valid classification match found.").show();
                }
            })
            .catch(error => {
                console.error("Error in fetch:", error);
                $("#error").text("An error occurred while processing your request.").show();
            });
    });

    // Trigger Dropzone processing on button click
    $("#submitBtn").on("click", function (e) {
        e.preventDefault(); // Prevent default form submission
        if (dz.files.length === 0) {
            $("#error").text("Please upload an image before submitting.").show();
            return;
        }
        dz.processQueue();
    });
}

$(document).ready(function () {
    console.log("Document is ready!");
    $("#error").hide();
    $("#resultHolder").hide();
    $("#divClassTable").hide();

    init();
});
