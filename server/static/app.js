Dropzone.autoDiscover = false;

function init() {
    let dz = new Dropzone("#dropzone", {
        url: "/CLASSIFY_IMAGES", // Correct Flask endpoint
        method: "post",
        maxFiles: 1,
        addRemoveLinks: true,
        dictDefaultMessage: "Drop an image here to classify",
        autoProcessQueue: false
    });

    // Ensure only one file is uploaded at a time
    dz.on("addedfile", function (file) {
        if (dz.files[1] != null) {
            dz.removeFile(dz.files[0]);
        }
    });

    // Handle file upload and send Base64 image data
    dz.on("addedfile", function (file) {
        let reader = new FileReader();
        reader.onload = function (event) {
            file.dataURL = event.target.result; // Assign Base64 data
        };
        reader.readAsDataURL(file);
    });

    dz.on("complete", function (file) {
        if (!file.dataURL) {
            console.error("File dataURL not available");
            $("#error").show();
            return;
        }

        let imageData = file.dataURL; // Base64 encoded image
        let url = "/CLASSIFY_IMAGES"; // Flask endpoint

        // Prepare FormData for the POST request
        let formData = new FormData();
        formData.append("image_data", imageData);

        fetch(url, {
            method: "POST",
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error("Network response was not ok");
            }
            return response.json();
        })
        .then(data => {
            console.log(data);
            if (!data || data.length === 0) {
                $("#resultHolder").hide();
                $("#divClassTable").hide();
                $("#error").show();
                return;
            }

            // Process the classification results
            let players = ["lebron_james", "michael_jordan", "shaq", "steph_curry"];
            let match = null;
            let bestScore = -1;

            for (let i = 0; i < data.length; ++i) {
                let maxScoreForThisClass = Math.max(...data[i].class_probability);
                if (maxScoreForThisClass > bestScore) {
                    match = data[i];
                    bestScore = maxScoreForThisClass;
                }
            }

            if (match) {
                $("#error").hide();
                $("#resultHolder").show();
                $("#divClassTable").show();
                $("#resultHolder").html($(`[data-player="${match.class}"`).html());
                let classDictionary = match.class_dictionary;
                for (let personName in classDictionary) {
                    let index = classDictionary[personName];
                    let probabilityScore = match.class_probability[index];
                    let elementName = "#score_" + personName;
                    $(elementName).html(probabilityScore);
                }
            }
        })
        .catch(error => {
            console.error("Error in fetch:", error);
            $("#error").show();
        });
    });

    // Trigger Dropzone processing on button click
    $("#submitBtn").on("click", function (e) {
        e.preventDefault(); // Prevent default form submission
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
