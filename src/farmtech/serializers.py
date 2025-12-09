"""
Serializer classes for FarmTech app.
"""

from rest_framework import serializers
from geonode.geoapps.models import GeoApp


class DatasetUpdateSerializer(serializers.Serializer):
    """
    Serializer class for updating a dataset with an Excel file.
    """

    dataset_name = serializers.CharField(
        max_length=255, required=True, help_text="Name of the dataset to update"
    )
    excel_file = serializers.FileField(
        required=True, help_text="Excel file containing the data to import"
    )

    def validate_excel_file(self, value):
        """
        Validate that the file is a valid Excel file.
        """

        allowed_extensions = [".xlsx", ".xls"]
        file_name = value.name.lower()

        if not any(file_name.endswith(ext) for ext in allowed_extensions):
            raise serializers.ValidationError(
                "The file must be an Excel file (.xlsx or .xls)"
            )

        return value


class GroupJoinRequestSerializer(serializers.Serializer):
    """
    Serializer for the join request to a Group Profile.
    """

    group_profile_id = serializers.IntegerField(
        required=True, help_text="ID of the GroupProfile to join"
    )

    requested_role = serializers.ChoiceField(
        choices=["manager", "member"],
        required=True,
        help_text="Role requested: 'manager' or 'member'",
    )

    motivation = serializers.CharField(
        required=True,
        allow_blank=False,
        min_length=10,
        help_text="Motivation for the join request (min 10 characters)",
    )

    def validate_motivation(self, value):
        """
        Validate that the motivation is not empty or only contains white spaces.
        """
        if not value or not value.strip():
            raise serializers.ValidationError(
                "The motivation cannot be empty or only contain white spaces"
            )
        return value.strip()


class DashboardPublishSerializer(serializers.ModelSerializer):
    """
    Serializer for updating the is_published field of a GeoApp.
    """

    class Meta:
        """
        Meta class for DashboardPublishSerializer.
        """

        model = GeoApp
        fields = ["is_published"]


class GroupExcelTemplatesSerializer(serializers.Serializer):
    """
    Serializer for getting the Excel templates of a Group Profile.
    """

    group_profile_id = serializers.IntegerField(
        required=True, help_text="ID of the GroupProfile to get the Excel templates"
    )


class DataForInferenceSerializer(serializers.Serializer):
    """
    Serializer class for inputting a tiff file for inference.
    """

    tiff_file = serializers.FileField(
        required=False, help_text="Input tiff file for inference"
    )
    polygon = serializers.DictField(
        required=False, help_text="Input polygon for inference"
    )
    start_date = serializers.DateField(
        required=False, help_text="Start date for the input data range"
    )
    end_date = serializers.DateField(
        required=False, help_text="End date for the input data range"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_type = None

    def validate(self, attrs):
        tiff_file_provided = attrs.get("tiff_file") is not None
        polygon_provided = attrs.get("polygon") != {}
        start_date_provided = attrs.get("start_date") is not None
        end_date_provided = attrs.get("end_date") is not None

        if not (tiff_file_provided or polygon_provided):
            raise serializers.ValidationError(
                "Either 'tiff_file' or 'polygon' must be provided."
            )
        if tiff_file_provided and polygon_provided:
            raise serializers.ValidationError(
                "Only one of 'tiff_file' or 'polygon' should be provided."
            )
        if polygon_provided and not (start_date_provided and end_date_provided):
            raise serializers.ValidationError(
                "If 'polygon' is provided, 'start_date' and 'end_date' must be provided."
            )

        if tiff_file_provided:
            self.input_type = "tiff"
        else:
            self.input_type = "polygon"

        return attrs
